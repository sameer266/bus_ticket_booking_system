from django.db import models
from django.apps import apps  # For lazy importing models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone


class Route(models.Model):
    source = models.CharField(max_length=255, null=False, help_text="Starting point of the route")
    destination = models.CharField(max_length=255, null=False, help_text="Ending point of the route")
    distance = models.DecimalField(max_digits=6, decimal_places=2, help_text="Distance in kilometers")
    estimated_time = models.TimeField(null=True, help_text="Estimated travel time (hh:mm:ss)")

    def __str__(self):
        return f"{self.source} to {self.destination} - {self.distance} km"


        



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
        
        super().save(*args, **kwargs)


# ====== schedule =========

class Schedule(models.Model):
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE)
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    departure_time = models.DateTimeField(null=True, blank=True, help_text="Time when bus starts")
    arrival_time = models.DateTimeField(null=True, blank=True, help_text="Expected arrival time")
    date = models.DateTimeField(null=True,blank=True,help_text="Date and time of the journey (Y-M-D H:M:S)",editable=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Ticket price")
    
    def save(self,*args,**kargs):
        if not self.date:
            self.date=timezone.now()
        super().save(*args,**kargs)
            
   
    def __str__(self):
        return f"{self.bus.bus_number} | {self.route.source} to {self.route.destination} at {self.date.strftime('%Y-%m-%d %H:%M:%S')}"


@receiver(post_save,sender=Schedule)
def create_bus_admin_and_trip(sender,instance,created,**kwargs):
    if created:
        BusAdmin=apps.get_model('bus','BusAdmin')
        bus_admin=BusAdmin.objects.filter(bus=instance.bus).first()
        if not bus_admin:
            CustomUser=apps.get_model('custom_user','CustomUser')
            new_user=CustomUser.objects.create_user(
                email=f"busadmin_{instance.bus.bus_number.lower().replace(' ','_')}@example.com",
                pasword="Sameer123",
                role="bus_admin"
            )
            bus_admin=BusAdmin.objects.create(user=new_user,bus=instance.bus)
    
    # Create a Trip 
    trip =Trip.objects.filter(bus=instance.bus).first()
    if not trip:
        Trip.objects.create(bus=instance.bus,route=instance.route,
                            driver=instance.bus.driver,
                            scheduled_departure=instance.departure_time,
                            scheduled_arrival=instance.arrival_time)