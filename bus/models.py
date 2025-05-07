from django.db import models
from multiselectfield import MultiSelectField
from django.core.exceptions import ValidationError
from django.apps import apps
from route.models import Schedule

# Importing related models
from custom_user.models import CustomUser,TransportationCompany



# ========= Ticket Counter Model ===========
class TicketCounter(models.Model):
    """
    Represents a ticket counter managed by a sub-admin.
    """
    user = models.OneToOneField(
        'custom_user.CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'sub_admin'},
        related_name="ticket_counter"
    )
    counter_name = models.CharField(max_length=200, default="None", help_text="Name of Ticket Counter")
    bank_account = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Bank account number for payments"
    )
    bank_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        help_text="Name of the bank"
    )
    
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.counter_name} - {self.location}"


# =========== Driver Model ===============
class Driver(models.Model):
    """
    Represents a driver with their profile and license details.
    """
    transportation_company=models.ForeignKey(TransportationCompany,on_delete=models.CASCADE,null=True,blank=True)
    # ticket_counter=models.ForeignKey(TicketCounter,on_delete=models.CASCADE,null=True,blank=True)
    full_name = models.CharField(max_length=255, null=False)
    driver_profile = models.ImageField(upload_to="driver_profile/",null=True,blank=True)
    license_image = models.ImageField(upload_to="driver_license/")
    phone_number = models.CharField(max_length=10, unique=True, null=False)

    def delete(self, *args, **kwargs):
        """
        Deletes associated image files before deleting the model.
        """
        if self.driver_profile:
            self.driver_profile.delete(save=False)
        if self.license_image:
            self.license_image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Driver: {self.full_name} - {self.phone_number}"


# =========== Staff Model ===============
class Staff(models.Model):
    """
    Represents a staff member with optional profile and staff card images.
    """
    transportation_company=models.ForeignKey(TransportationCompany,on_delete=models.CASCADE,null=True,blank=True)
    # ticket_counter=models.ForeignKey(TicketCounter,on_delete=models.Case,null=True,blank=False)
    full_name = models.CharField(max_length=255, null=False)
    staff_profile = models.ImageField(upload_to="staff_profile/", null=True, blank=True)
    staff_card = models.ImageField(upload_to="staff_card/", null=True, blank=True)
    phone_number = models.CharField(max_length=10, unique=True, null=False)

    def delete(self, *args, **kwargs):
        """
        Deletes associated profile image before deleting the model.
        """
        if self.staff_profile:
            self.staff_profile.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Staff: {self.full_name} - {self.phone_number}"


# ====== Bus Model =============
class Bus(models.Model):
    """
    Represents a bus with its details, features, and associated driver/staff.
    """
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
        ("charging", "Charging"),
        ("fan", "Fan"),
        ("wifi", "WiFi"),
    )
    transportation_company=models.ForeignKey(TransportationCompany,on_delete=models.CASCADE,null=True,blank=True)

    driver = models.OneToOneField(Driver, on_delete=models.CASCADE, null=True, blank=True)
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, null=True, blank=True)
   
    bus_number = models.CharField(max_length=20, unique=True, null=False, help_text="Example: BA 1 KHA 1234")
    bus_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default="deluxe_bus")
    features = MultiSelectField(choices=FEATURE_CHOICES, null=True, blank=True)
    bus_image = models.ImageField(upload_to="bus_images/")
    total_seats = models.PositiveIntegerField(default=35)
   
    is_active = models.BooleanField(default=True, help_text="Indicates if the bus is active")
    
 

        
    # def save(self, *args, **kwargs):
    #     """
    #     Ensures available seats do not exceed total seats.
    #     """
    #     if self.available_seats > self.total_seats:
    #         raise ValidationError("Available seats cannot exceed total seats.")
    #     super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Deletes associated image file before deleting the model.
        """
        if self.bus_image and self.bus_image.storage.exists(self.bus_image.name):
            self.bus_image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.bus_number}"


# ======== Seat Layout Model ===========
class SeatLayoutBooking(models.Model):
    """
    Represents a booking for a specific seat layout.
    """
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True)
    layout_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


     # Method to update seat status in the seat layout (Mark as available)
     
    def mark_seat_available(self, seat_keys):
        """
        Mark the seats as available in the seat layout.
        Accepts a list of seat keys.
        """
        for seat_key in seat_keys:
            found = False
            for row in self.layout_data:
                for seat in row:
                   
                    if isinstance(seat, dict) and seat["seat"] == seat_key:
                        if seat["status"] == "booked":
                            seat["status"] = "available"
                            found = True
                            print(f"Seat {seat_key} is now available.")
                        else:
                            print(f"Seat {seat_key} is already available.")
                        break  # No need to continue if we've found the seat
                if found:
                    break  # Exit the outer loop if seat is found and updated
            if not found:
                print(f"Seat {seat_key} not found in layout.")
        self.save()

    def mark_seat_booked(self, seat_keys):
        """
        Mark the seats as booked in the seat layout.
        Accepts a list of seat keys.
        """
        
        for seat_key in seat_keys:
            found = False
            for row in self.layout_data:
                print(seat_key)
                
                for seat in row:
                    if isinstance(seat, dict) and seat["seat"] == seat_key:
                        if seat["status"] == "available":
                            seat["status"] = "booked"
                            found = True
                            print(f"Seat {seat_key} is now booked.")
                        else:
                            print(f"Seat {seat_key} is already booked.")
                        break  # No need to continue if we've found the seat
                if found:
                    break  # Exit the outer loop if seat is found and updated
            if not found:
                print(f"Seat {seat_key} not found in layout.")
        self.save()
        
        
    def __str__(self):
        return f"{self.schedule.bus} ({self.created_at})"

    class Meta:
        ordering = ['-created_at']

    
# ========= Bus Layout Model =========
class BusLayout(models.Model):
    """
    Represents the seating layout of a bus.
    """

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE,null=True,blank=True)
    rows = models.PositiveIntegerField()
    column = models.PositiveIntegerField()
    aisle_column = models.PositiveIntegerField()
    layout_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bus} ({self.created_at})"

    class Meta:
        ordering = ['-created_at']


# ======= Bus Admin Model ============
class BusAdmin(models.Model):
    """
    Represents a bus admin responsible for managing a bus and its operations.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="bus_admin_profile",
        limit_choices_to={'role': 'bus_admin'}
    )
    bus = models.OneToOneField(
        'Bus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Bus assigned to this admin"
    )
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True)
    booked_seats = models.PositiveIntegerField(default=0, help_text="Number of seats booked")
    remaining_seats = models.PositiveIntegerField(default=0, help_text="Calculated remaining seats")
    estimated_arrival = models.DateTimeField(null=True, blank=True, help_text="Estimated Arrival time")
    last_updated = models.DateTimeField(auto_now=True, help_text="Timestamp of last update")
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Ticket price")
    source = models.CharField(max_length=255, null=True, blank=True, help_text="Starting point of the journey")
    destination = models.CharField(max_length=255, null=True, blank=True, help_text="Ending point of the journey")

    def save(self, *args, **kwargs):
        """
        Ensures remaining seats are calculated and updates related models.
        """
        if self.driver:
            self.bus.driver = self.driver
            self.bus.save()

        if self.bus:
            if self.booked_seats > self.bus.total_seats:
                raise ValidationError("Booked seats cannot exceed total seats on the bus.")

            self.remaining_seats = self.bus.total_seats - self.booked_seats
            self.bus.available_seats = self.remaining_seats
            self.bus.is_running = True
            self.bus.save()

            if self.source is None:
                self.source = self.bus.route.source
            if self.destination is None:
                self.destination = self.bus.route.destination

            if self.price:
                schedules = apps.get_model('bus', 'Schedule').objects.filter(bus=self.bus)
                for schedule in schedules:
                    schedule.price = self.price
                    schedule.save()

        super().save(*args, **kwargs)

    def clean(self):
        if self.driver and not Driver.objects.filter(id=self.driver.id).exists():
            raise ValidationError("The specified driver does not exist.")
        if self.staff and not Staff.objects.filter(id=self.staff.id).exists():
            raise ValidationError("The specified staff does not exist.")

    def __str__(self):
        eta = self.estimated_arrival.strftime('%Y-%m-%d %H:%M:%S') if self.estimated_arrival else "N/A"
        return f"Bus Admin: {self.user.full_name} | Bus: {self.bus.bus_number if self.bus else 'No Bus Assigned'}"


# ========= Vehicle Type Model ============
class VechicleType(models.Model):
    """
    Represents different types of vehicles.
    """
    name = models.CharField(max_length=100)
    image=models.ImageField(upload_to="vechicle_type_images/",null=True,blank=True)
    
    def delete(self, *args, **kwargs):
        """
        Deletes associated image file before deleting the model.
        """
        if self.image and self.image.storage.exists(self.image.name):
            self.image.delete(save=False)
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


# =========== Vehicle Reservation Model ===============
class BusReservation(models.Model):
    """
    Represents a reservation for a bus or vehicle.
    """
   
    transportation_company=models.ForeignKey(TransportationCompany,on_delete=models.CASCADE,null=True,blank=True)
    
    name=models.CharField(max_length=100,default="None")
    type = models.ForeignKey(VechicleType, on_delete=models.CASCADE, null=True, blank=True)
    vechicle_number = models.CharField(max_length=100, default="None")
    vechicle_model=models.CharField(max_length=100,default="None")
    image = models.ImageField(upload_to="vechicle_images/",null=True, blank=True)
    document=models.ImageField(upload_to="vechicle_document/",null=True,blank=True)
    color=models.CharField(max_length=100,null=True,blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
    total_seats = models.PositiveIntegerField(default=35)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    source=models.CharField(max_length=200,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
   

    def delete(self, *args, **kwargs):
        """
        Deletes associated image file before deleting the model.
        """
        if self.image and self.image.storage.exists(self.image.name):
            self.image.delete(save=False)
        super().delete(*args, **kwargs)
        
    
        
       

    def __str__(self):
        return f"Reservation {self.vechicle_number}"
