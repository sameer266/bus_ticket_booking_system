from django.db import models
from django.apps import apps  # For lazy importing models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
import random


class SubRoutes(models.Model):
    name=models.CharField(max_length=100)
    
    def __str__(self):
        return f"Subroutes {self.name}"


# ======== route ============
class Route(models.Model):
    MAX_SUBROUTES = 5

    source = models.CharField(max_length=255, null=False)
    image = models.ImageField(upload_to="route-img/", null=True, blank=True)
    sub_routes = models.ManyToManyField(SubRoutes, blank=True)
    destination = models.CharField(max_length=255, null=False)
    distance = models.DecimalField(max_digits=6, decimal_places=2)
    description=models.TextField(null=True)
    estimated_time = models.PositiveIntegerField(null=True, default=0)

    def clean(self):
        if self.pk and self.sub_routes.count() > self.MAX_SUBROUTES:
            raise ValidationError(f"Maximum {self.MAX_SUBROUTES} sub-routes allowed per route.")

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.source} to {self.destination} - {self.distance} km"





# ========== RouteSubRoute (Used for seacrhing the sub routes) ============
class SearchSubRoute(models.Model):
    route=models.ForeignKey(Route,on_delete=models.CASCADE)
    subroute=models.ForeignKey(SubRoutes,on_delete=models.CASCADE)
    order=models.PositiveBigIntegerField(null=True,blank=True)
    
    class Meta:
        ordering= ['order']
        unique_together=('route','subroute') 
           
    def save(self,*args,**kwargs):
        if self.order is None:
            last_order=SearchSubRoute.objects.filter(route=self.route).aggregate(models.Max('order'))['order__max']
            self.order=(last_order or  0) + 1
        super().save(*args,**kwargs)
    
    def __str__(self):
        return  f"{self.route} via {self.subroute} (Order {self.order})"
    
    @staticmethod
    def find_routes_with_subroute_order(start_name ,end_name):
        """Returns all parent routes where `start_name` appears before `end_name` in order."""
        start_matches=SearchSubRoute.objects.filter(subroute__name=start_name)
        valid_routes=[]
        for start in start_matches:
            try:
                end=SearchSubRoute.objects.get(route=start.route,subroute__name=end_name)
                if start.order<end.order:
                    valid_routes.append(start.route)
            except SearchSubRoute.DoesNotExist:
                continue
        return valid_routes
        
        
    
# =========== Trip ==============
class Trip(models.Model):
    """
    Represents a trip for a specific bus on a specific route, with scheduled and actual timings.
    """
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    driver = models.ForeignKey('bus.Driver', on_delete=models.CASCADE, help_text="Driver of the bus")
    staff=models.ForeignKey('bus.Staff',on_delete=models.CASCADE,null=True,blank=True)
    schedule=models.ForeignKey('route.Schedule',on_delete=models.CASCADE,null=True,blank=True)
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
    created_at=models.DateTimeField(auto_now_add=True,null=True,blank=True)

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
    CHOICES=(
        ("upcoming","Upcoming"),
        ("ongoing","Ongoing"),
        ("finished","Finished")
    )
    transportation_company=models.ForeignKey('custom_user.TransportationCompany',on_delete=models.CASCADE,null=True,blank=True)
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    departure_time = models.DateTimeField(null=True, blank=True, help_text="Time when bus starts")
    arrival_time = models.DateTimeField(null=True, blank=True, help_text="Expected arrival time")
    date = models.DateTimeField(null=True, blank=True, help_text="Date and time of the journey (Y-M-D H:M:S)", editable=False)
    shift = models.CharField(max_length=5, choices=[('day', 'Day'), ('night', 'Night')],null=True,blank=True)
    sale_price=models.DecimalField(max_digits=8,decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Ticket price")
    available_seats = models.PositiveIntegerField(default=0, help_text="Number of available seats")
    status=models.CharField(max_length=20,null=True,blank=True)
    

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()

        if self.departure_time:
            hour = self.departure_time.hour
            if 6 <= hour < 18:  # Between 6 AM and 6 PM
                self.shift = 'day'
            else:
                self.shift = 'night'

        super().save(*args, **kwargs)

       
        
    def delete(self, *args, **kwargs):
        Trip = apps.get_model('route', 'Trip')
        BusAdmin = apps.get_model('bus', 'BusAdmin')

        # Delete corresponding trip
        trip = Trip.objects.filter(bus=self.bus, route=self.route, scheduled_departure=self.departure_time)
        if trip.exists():
            trip.delete()

        # Delete BusAdmin if no other schedules exist for this bus
        if not Schedule.objects.filter(bus=self.bus).exclude(id=self.id).exists():
            bus_admin = BusAdmin.objects.filter(bus=self.bus)
            if bus_admin.exists():
                bus_admin.delete()

        super().delete(*args, **kwargs)

        
    # --- To udpate the status of schedule according to time --
    @staticmethod
    def update_all_status():
        now=timezone.now()
        Schedule.objects.filter(departure_time__gt=now).update(status="upcoming")
        Schedule.objects.filter(departure_time__lte=now,arrival_time__gt=now).update(status='ongoing')
        Schedule.objects.filter(arrival_time__lte=now).update(status="finished")
        

    def __str__(self):
        return f"{self.bus.bus_number} | {self.route.source} to {self.route.destination} at {self.departure_time } {self.status}"


@receiver(post_save, sender=Schedule)
def create_bus_admin_and_trip(sender, instance, created, **kwargs):
    """
    Signal to create a BusAdmin and Trip when a new Schedule is created.
    """
    
            
    if created:
        BusAdmin = apps.get_model('bus', 'BusAdmin')
        CustomUser = apps.get_model('custom_user', 'CustomUser')
        Commission=apps.get_model('booking','Commission')
        
        commission=Commission.objects.get(bus=instance.bus)
        commission.schedule=instance
        commission.save()
        
        # Create BusAdmin if not exists
        bus_admin = BusAdmin.objects.filter(bus=instance.bus).first()
        if not bus_admin:
            print("=== Bus Admin Create  ===")
            new_user, _ = CustomUser.objects.get_or_create(
                email=f"busadmin_{instance.bus.bus_number.lower().replace(' ', '_')}@example.com",
                
                password= f"Driver@{instance.bus.contact_number}",
                phone= instance.bus.contact_number,
                role="bus_admin",
                
            )
            print("Sinal-------sd")
            BusAdmin.objects.create(
                user=new_user,
                bus=instance.bus,
                driver=instance.bus.driver,
                source=instance.route.source,
                destination=instance.route.destination,
            )
        print("------- trip -------")
        # Create Trip if not exists
        trip = Trip.objects.filter(bus=instance.bus, route=instance.route, scheduled_departure=instance.departure_time).first()
        if not trip:
            Trip.objects.create(
                bus=instance.bus,
                route=instance.route,
                driver=instance.bus.driver,
                staff=instance.bus.staff,
                schedule=instance,
                scheduled_departure=instance.departure_time,
                scheduled_arrival=instance.arrival_time,
            )
            print('___________')


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


# ==========Notification ============
class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('system', 'System'),
        ('booking', 'Booking'),     
    ]
    
    user = models.ForeignKey('custom_user.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=NOTIFICATION_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  


    @staticmethod
    def send_notification_to_all_users(title, message):
        """
        Sends a notification to all users.
        """
        CustomUser = apps.get_model('custom_user', 'CustomUser')
        users = CustomUser.objects.filter(role='customer')
        for user in users:
            Notification.objects.create(user=user, title=title, message=message, type='system')
            
    def __str__(self):
        return f"{self.user.full_name} - {self.title}"
    
    