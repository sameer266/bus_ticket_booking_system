from django.db import models

# Create your models here.
from django.db import models
from custom_user.models import CustomUser
from route.models import Route
from django.core.exceptions import ValidationError


class TicketCounter(models.Model):
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.CASCADE,limit_choices_to={'role':'sub_admin'},related_name="ticket_counter")
    counter_name=models.CharField(max_length=200, default="None",help_text="Name of Ticket Counter name")
    location=models.CharField(max_length=100)
    created_at=models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
def __str__(self):
    return f"{self.counter_name} - {self.location}"


class Driver(models.Model):
    full_name = models.CharField(max_length=255, null=False)
    driver_profile = models.ImageField(upload_to="driver_profile/")
    license_image = models.ImageField(upload_to="driver_license/")
    phone_number = models.CharField(max_length=10, unique=True, null=False)

    def __str__(self):
        return f"Driver: {self.full_name} - {self.phone_number}"

class Staff(models.Model):
    full_name = models.CharField(max_length=255, null=False)
    staff_profile = models.ImageField(upload_to="staff_profile/", null=True, blank=True)  # Optional profile image
    phone_number = models.CharField(max_length=10, unique=True, null=False)

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

    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)  # A bus has one driver (optional)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)  # A bus has one staff (optional)
    bus_number = models.CharField(max_length=20, unique=True, null=False, help_text="Example: BA 1 KHA 1234")
    bus_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default="deluxe_bus")
    bus_image = models.ImageField(upload_to="bus_images/")
    total_seats = models.PositiveIntegerField(default=35)
    available_seats = models.PositiveIntegerField(default=35)
    route = models.OneToOneField(Route, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    is_running=models.BooleanField(default=False,help_text="To ensure the bus is in running state or not")

    def __str__(self):
        return f"{self.bus_number}" 

    def save(self, *args, **kwargs):
        """Ensure available seats don't exceed total seats."""
        if self.available_seats > self.total_seats:
            raise ValidationError("Available seats cannot exceed total seats.")
        super().save(*args, **kwargs)


# ======= Bus Admin ============
class BusAdmin(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="bus_admin_profile",
        limit_choices_to={'role': 'bus_admin'}  # Restricts only users with "bus_admin" role
    )
    bus=models.OneToOneField('Bus',on_delete=models.SET_NULL,null=True,blank=True,help_text="Bus assigned to  this admin")
    
    def __str__(self):
        return f"Bus Admin: {self.user.full_name} - {self.bus.bus_number if self.bus else 'No Bus Assigned'}"