from django.db import models
from django.apps import apps  # For lazy importing models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
import random


# ======= Route ==========
class Route(models.Model):
    """
    Represents a route with a source, destination, distance, and estimated travel time.
    """
    source = models.CharField(max_length=255, null=False, help_text="Starting point of the route")
    image=models.ImageField(upload_to="route-img/",null=True,blank=True)
    destination = models.CharField(max_length=255, null=False, help_text="Ending point of the route")
    distance = models.DecimalField(max_digits=6, decimal_places=2, help_text="Distance in kilometers")
    estimated_time = models.TimeField(null=True, help_text="Estimated travel time (hh:mm:ss)")

    def delete(self,*args,**kwargs):
        """ Delete the Image  """
        if self.image:
            self.image.delete(save=False)
        super().delete(*args,**kwargs)
        
    def __str__(self):
        return f"{self.source} to {self.destination} - {self.distance} km"

    
        
# =========== Trip ==============
class Trip(models.Model):
    """
    Represents a trip for a specific bus on a specific route, with scheduled and actual timings.
    """
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    driver = models.ForeignKey('bus.Driver', on_delete=models.CASCADE, help_text="Driver of the bus")
    
    # Scheduled trip details
    scheduled_departure = models.DateTimeField(help_text="Scheduled departure time of the bus")
    scheduled_arrival = models.DateTimeField(help_text="Scheduled arrival time of the bus")
    
    # Actual trip details
    actual_departure = models.DateTimeField(null=True, blank=True, help_text="Actual departure time of the bus")
    actual_arrival = models.DateTimeField(null=True, blank=True, help_text="Actual arrival time of the bus")

    # Status of the trip
    status = models.CharField(
        max_length=20,
        choices=[('on_time', 'On Time'), ('delayed', 'Delayed'), ('completed', 'Completed')],
        default='on_time',
        help_text="Current status of the trip"
    )

    def __str__(self):
        return f"Trip from {self.route.source} to {self.route.destination} on Bus {self.bus.bus_number}"

    def clean(self):
        """
        Custom clean method to update the trip status based on actual and scheduled timings.
        """
        if self.actual_departure and self.scheduled_departure:
            if self.actual_departure > self.scheduled_departure:
                self.status = 'delayed'
            elif self.actual_departure <= self.scheduled_departure:
                self.status = 'on_time'
            
            if self.actual_arrival:
                self.status = 'completed'

    def save(self, *args, **kwargs):
        """
        Custom save method to update the trip status based on actual and scheduled timings.
        """
        self.clean()
        super().save(*args, **kwargs)


# ====== Schedule =========
class Schedule(models.Model):
    """
    Represents a schedule for a bus on a specific route with departure and arrival times.
    """
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    departure_time = models.DateTimeField(null=True, blank=True, help_text="Time when bus starts")
    arrival_time = models.DateTimeField(null=True, blank=True, help_text="Expected arrival time")
    date = models.DateTimeField(null=True, blank=True, help_text="Date and time of the journey (Y-M-D H:M:S)", editable=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Ticket price")

    def save(self, *args, **kwargs):
        """
        Custom save method to update the bus route and set the schedule date if not provided.
        """
        if not self.date:
            self.date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Custom delete method to remove associated Trip and BusAdmin records when a schedule is deleted.
        """
        Trip = apps.get_model('route', 'Trip')
        BusAdmin = apps.get_model('bus', 'BusAdmin')

        # Delete the corresponding trip for this specific schedule
        trip = Trip.objects.filter(bus=self.bus, route=self.route, scheduled_departure=self.departure_time)
        if trip.exists():
            trip.delete()

        # Delete the corresponding BusAdmin if no other schedules exist for this bus
        if not Schedule.objects.filter(bus=self.bus).exclude(id=self.id).exists():
            bus_admin = BusAdmin.objects.filter(bus=self.bus)
            if bus_admin.exists():
                bus_admin.delete()

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.bus.bus_number} | {self.route.source} to {self.route.destination} at {self.date.strftime('%Y-%m-%d %H:%M:%S')}"


@receiver(post_save, sender=Schedule)
def create_bus_admin_and_trip(sender, instance, created, **kwargs):
    """
    Signal to create a BusAdmin and Trip when a new Schedule is created.
    """
    if created:
        BusAdmin = apps.get_model('bus', 'BusAdmin')
        CustomUser = apps.get_model('custom_user', 'CustomUser')
        Trip = apps.get_model('route', 'Trip')

        # Create BusAdmin if not exists
        bus_admin = BusAdmin.objects.filter(bus=instance.bus).first()
        if not bus_admin:
            new_user, _ = CustomUser.objects.get_or_create(
                email=f"busadmin_{instance.bus.bus_number.lower().replace(' ', '_')}@example.com",
                defaults={
                    "password": "DefaultPassword123",
                    "phone": random.randint(9000000000, 9999999999),
                    "role": "bus_admin",
                },
            )
            BusAdmin.objects.create(
                user=new_user,
                bus=instance.bus,
                driver=instance.bus.driver,
                source=instance.route.source,
                destination=instance.route.destination,
            )

        # Create Trip if not exists
        trip = Trip.objects.filter(bus=instance.bus, route=instance.route, scheduled_departure=instance.departure_time).first()
        if not trip:
            Trip.objects.create(
                bus=instance.bus,
                route=instance.route,
                driver=instance.bus.driver,
                scheduled_departure=instance.departure_time,
                scheduled_arrival=instance.arrival_time,
            )


# ======== Customer Review ============
class CustomerReview(models.Model):
    """
    Represents a customer review for a bus, including rating and optional comments.
    """
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        'custom_user.CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'}
    )  # Assuming users are registered
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.full_name} for {self.bus.bus_number} - {self.rating}⭐"
