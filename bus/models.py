from django.db import models
from multiselectfield import MultiSelectField
import os

# Create your models here.
from django.db import models
from custom_user.models import CustomUser
from route.models import Route,Trip
from django.core.exceptions import ValidationError
from django.apps import apps


# ========= Ticket Counter ===============
class TicketCounter(models.Model):
    user=models.OneToOneField('custom_user.CustomUser',on_delete=models.CASCADE,limit_choices_to={'role':'sub_admin'},related_name="ticket_counter")
    counter_name=models.CharField(max_length=200, default="None",help_text="Name of Ticket Counter name")
    location=models.CharField(max_length=100)
    created_at=models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
def __str__(self):
    return f"{self.counter_name} - {self.location}"

# =========== Driver ===============
class Driver(models.Model):
    full_name = models.CharField(max_length=255, null=False)
    driver_profile = models.ImageField(upload_to="driver_profile/")
    license_image = models.ImageField(upload_to="driver_license/")
    phone_number = models.CharField(max_length=10, unique=True, null=False)
    
    def delete(self, *args, **kwargs):
        # Delete the associated image file before deleting the model
        if self.driver_profile:
            self.driver_profile.delete(save=False)
        if self.license_image:
            self.license_image.delete(save=False)
            
        super().delete(*args,**kwargs)

    def __str__(self):
        return f"Driver: {self.full_name} - {self.phone_number}"


# =========== Staff ===============
class Staff(models.Model):
    full_name = models.CharField(max_length=255, null=False)
    staff_profile = models.ImageField(upload_to="staff_profile/", null=True, blank=True)  # Optional profile image
    staff_card=models.ImageField(upload_to="staff_card/",null=True,blank=True)
    phone_number = models.CharField(max_length=10, unique=True, null=False)
    


    def delete(self,*args,**kwargs):
        if self.staff_profile:
            self.staff_profile.delete(save=False)
        super().delete(*args,**kwargs)
        
    def __str__(self):
        return f"Staff: {self.full_name} - {self.phone_number}"
    
    


# ====== Bus =============
class Bus(models.Model):
    VEHICLE_CHOICES = (
        ("tourist_bus", "Tourist Bus"),
        ("express_bus", "Express Bus"),
        ("deluxe_bus", "Deluxe Bus"),
        ("mini_bus", "Mini Bus"),
        ("micro_bus", "Micro Bus"),
        ("electric_bus", "Electric Bus"),
    )
    FEATURE_CHOICES = (
        ("ac", "AC"),
        ("charging", "charging"),
        ("fan", "Fan"),
        ("wifi","Wifi"),      
    )

    driver = models.OneToOneField(Driver, on_delete=models.CASCADE, null=True, blank=True)  # A bus has one driver (optional)
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, null=True, blank=True)  # A bus has one staff (optional)
    route=models.ForeignKey(Route,on_delete=models.CASCADE,null=True,blank=True)
    bus_number = models.CharField(max_length=20, unique=True, null=False, help_text="Example: BA 1 KHA 1234")
    bus_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default="deluxe_bus")
    features = MultiSelectField(choices=FEATURE_CHOICES, null=True, blank=True)  # Allows multiple selections
    bus_image = models.ImageField(upload_to="bus_images/")
    total_seats = models.PositiveIntegerField(default=35)
    available_seats = models.PositiveIntegerField(default=35)
   
    is_active = models.BooleanField(default=False)
    is_running = models.BooleanField(default=False, help_text="To ensure the bus is in running state or not")
    
    def save(self, *args, **kwargs):
        """Ensure available seats don't exceed total seats."""
        if self.available_seats > self.total_seats:
            raise ValidationError("Available seats cannot exceed total seats.")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete the associated image file before deleting the model
        if self.bus_image:
            self.bus_image.delete(save=False)
        super().delete(*args,**kwargs)

    def __str__(self):
        return f"{self.bus_number}"

    

# ========= Bus Layout =========
class BusLayout(models.Model):
    bus=models.ForeignKey(Bus,on_delete=models.CASCADE,unique=True)
    rows=models.PositiveIntegerField(blank=False,null=False)
    column=models.PositiveIntegerField(blank=False,null=False)
    aisle_column=models.PositiveIntegerField(blank=False)
    layout_data=models.JSONField(
        default=list,
        blank=True
    )
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bus} ({self.created_at})"

    class Meta:
        ordering = ['-created_at']
    

# ======= Bus Admin ============
class BusAdmin(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="bus_admin_profile",
        limit_choices_to={'role': 'bus_admin'}  # Restricts only users with "bus_admin" role
    )
    bus = models.OneToOneField(
        'Bus', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        help_text="Bus assigned to this admin"
    )
    driver = models.OneToOneField(Driver, on_delete=models.CASCADE,null=True,blank=True)  # New field for the driver
    booked_seats = models.PositiveIntegerField(default=0, help_text="Number of seats booked")
    remaining_seats = models.PositiveIntegerField(default=0, help_text="Calculated remaining seats")
    estimated_arrival = models.DateTimeField(null=True, blank=True, help_text="Estimated Arrival time")
    last_updated = models.DateTimeField(auto_now=True, help_text="Timestamp of last update")
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Ticket price for the bus journey")
    source = models.CharField(max_length=255, null=True, blank=True, help_text="Starting point of the journey (overrides route source)")
    destination = models.CharField(max_length=255, null=True, blank=True, help_text="Ending point of the journey (overrides route destination)")
    
    def save(self, *args, **kwargs):
        """Ensure remaining seats are calculated, and  Update BusDriver and update Bus and Route models."""
        
        # Update Bus driver when BusAdmin is saved
        if self.driver:
            self.bus.driver = self.driver  # Assign the driver to the bus
            self.bus.save()  # Save the bus with the new driver
            
        if self.bus:
            if self.booked_seats > self.bus.total_seats:
                raise ValidationError("Booked seats cannot exceed total seats on the bus.")
            
            # Calculate remaining seats
            self.remaining_seats = self.bus.total_seats - self.booked_seats

            # Update the Bus model automatically
            self.bus.available_seats = self.remaining_seats
            self.bus.is_running = True  
            self.bus.save()

           # Update source/destination dynamically if not provided
            if self.source is None:
                self.source = self.bus.route.source
            if self.destination is None:
                self.destination = self.bus.route.destination

            # Update Schedule model price based on BusAdmin price
            if self.price:
                # Fetch related schedule and update price
                schedules = apps.get_model('bus', 'Schedule').objects.filter(bus=self.bus)
                for schedule in schedules:
                    schedule.price = self.price
                    schedule.save()

        super().save(*args, **kwargs)

    def __str__(self):
        eta = self.estimated_arrival.strftime('%Y-%m-%d %H:%M:%S') if self.estimated_arrival else "N/A"
        return f"Bus Admin: {self.user.full_name} | Bus: {self.bus.bus_number if self.bus else 'No Bus Assigned'} | Booked: {self.booked_seats} | Remaining: {self.remaining_seats} | ETA: {eta} | Price: {self.price} | Source: {self.source} | Destination: {self.destination}"


#=========== Bus Reservation ===============
class BusReservation(models.Model):
    
    STATUS_CHOICES=(
        ('booked','Booked'),
        ('cancelled','Cancelled')
    )
    bus=models.ForeignKey('bus.Bus',on_delete=models.CASCADE)
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.CASCADE)
    reservation_date=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=10,choices=STATUS_CHOICES,default='booked')

    
    @staticmethod
    def is_bus_available(bus):
            """
            Check if the bus is available for a new reservation within the requested time frame.
            If the trip spans multiple days, the start_time and end_time should account for that.
            """
            conflicting_trips = Trip.objects.filter(
                
                bus=bus,
               
            )
            
            if conflicting_trips.exists():
                return False
            return True

    
    def __str__(self):
        return f"Reservation fror {self.user.full_name} on {self.bus.bus_number}"
    