from django.db import models
from django.apps import apps  # For lazy importing models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone


# ======= Route ==========
class Route(models.Model):
    source = models.CharField(max_length=255, null=False, help_text="Starting point of the route")
    destination = models.CharField(max_length=255, null=False, help_text="Ending point of the route")
    distance = models.DecimalField(max_digits=6, decimal_places=2, help_text="Distance in kilometers")
    estimated_time = models.TimeField(null=True, help_text="Estimated travel time (hh:mm:ss)")

    def __str__(self):
        return f"{self.source} to {self.destination} - {self.distance} km"


        


# =========== Trip ==============
class Trip(models.Model):
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    driver = models.ForeignKey('bus.Driver', on_delete=models.CASCADE, help_text="Driver of the bus")
    # Scheduled trip details
    scheduled_departure = models.DateTimeField(help_text="Scheduled departure time of the bus")
    scheduled_arrival = models.DateTimeField(help_text="Scheduled arrival time of the bus")
    
    # Actual trip details
    actual_departure = models.DateTimeField(null=True, blank=True, help_text="Actual departure time of the bus")
    actual_arrival = models.DateTimeField(null=True, blank=True, help_text="Actual arrival time of the bus")

    status = models.CharField(max_length=20, choices=[('on_time', 'On Time'), ('delayed', 'Delayed'), ('completed', 'Completed')], default='on_time', help_text="Current status of the trip")

    def __str__(self):
        return f"Trip from {self.route.source} to {self.route.destination} on Bus {self.bus.bus_number}"

    def save(self, *args, **kwargs):
        if self.actual_departure and self.scheduled_departure:
            #  checking if the trip is delayed
            if self.actual_departure > self.scheduled_departure:
                self.status = 'delayed'
            
            # checking if trip is on_time
            if self.actual_departure <= self.scheduled_departure:
                self.status='on_time'
                
            if self.actual_arrival:
                self.status = 'completed'
        super().save(*args, **kwargs)


# ====== schedule =========
import random


class Schedule(models.Model):
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    departure_time = models.DateTimeField(null=True, blank=True, help_text="Time when bus starts")
    arrival_time = models.DateTimeField(null=True, blank=True, help_text="Expected arrival time")
    date = models.DateTimeField(null=True, blank=True, help_text="Date and time of the journey (Y-M-D H:M:S)", editable=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Ticket price")

    def save(self, *args, **kwargs):
        
        if self.bus:
            self.bus.route=self.route
            self.bus.save(update_fields=['route'])
            
        if not self.date:
            self.date = timezone.now()
        
        super().save(*args, **kwargs)
    
    # Delete Trip and BusAdmin when Schedule is deleted
    def delete(self, *args, **kwargs):
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
    if created:
        BusAdmin = apps.get_model('bus', 'BusAdmin')
        bus_admin = BusAdmin.objects.filter(bus=instance.bus).first()
        
        
        if not bus_admin:
            CustomUser = apps.get_model('custom_user', 'CustomUser')
            new_user=CustomUser.objects.get(email=f"busadmin_{instance.bus.bus_number.lower().replace(' ','_')}@example.com")
            print(new_user)
            if not new_user:
                new_user = CustomUser.objects.create_user(
                    email=f"busadmin_{instance.bus.bus_number.lower().replace(' ','_')}@example.com",
                    password="Sameer123",
                    phone=random.randint(9000000000, 9999999999),  # More realistic phone number
                    role="bus_admin",
                )
            
            bus_admin = BusAdmin.objects.create(user=new_user, bus=instance.bus, driver=instance.bus.driver, source=instance.route.source,
                                                destination=instance.route.destination)
    
    # Create a Trip only if one doesn't exist for this exact schedule
    Trip = apps.get_model('route', 'Trip')
    trip = Trip.objects.filter(bus=instance.bus, route=instance.route, scheduled_departure=instance.departure_time).first()
    
    if not trip:
        Trip.objects.create(
            bus=instance.bus,
            route=instance.route,
            driver=instance.bus.driver,
            scheduled_departure=instance.departure_time,
            scheduled_arrival=instance.arrival_time
        )

# ======== Customer Reiew ============
class CustomerReview(models.Model):
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey('custom_user.CustomUser', on_delete=models.CASCADE,limit_choices_to={'role':'customer'})  # Assuming users are registered
    route=models.ForeignKey(Route,on_delete=models.CASCADE,null=True,blank=True)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.full_name} for {self.bus.bus_number} - {self.rating}⭐"
