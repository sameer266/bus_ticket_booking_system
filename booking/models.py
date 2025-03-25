from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.apps import apps
from django.core.exceptions import ValidationError
from decimal import Decimal
from bus.models import Bus
from route.models import Schedule
from .tasks import release_unpaid_seat

# ==========================
# Models for Bus Seat Booking System
# ==========================

# ===== Seat Model =====
class Seat(models.Model):
    """
    Represents a seat in a bus.
    """
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked')
    )

    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE, help_text="Bus to which the seat belongs",
                            null=True,blank=True)  # Add this field
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="booked")
    seat_number = models.CharField(max_length=10, help_text="Seat number in the format 'A1'")
    
  
    class Meta:
        unique_together = ('seat_number', 'bus')  # Ensure unique seat numbers per bus

    def __str__(self):
        return f"Seat: {self.seat_number} | Status: {self.status}"
    
    

# ===== Booking Model =====
class Booking(models.Model):
    """
    Represents a booking made by a user for a specific seat on a bus.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('booked', 'Booked'),
        ('reserved','Reserved'),
        ('canceled', 'Canceled')
    )

    user = models.ForeignKey(
        'custom_user.CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'}
    )
    payment=models.ForeignKey('booking.Payment',on_delete=models.Case,null=True,blank=True)
    seat = models.JSONField(default=list)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='booking',null=True,blank=True)
    schedule = models.ForeignKey(
        'route.Schedule',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    booking_status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    booked_at = models.DateTimeField(auto_now_add=True)
   

    def __str__(self):
        return f"Booking #{self.id} - Seat: {self.seat} - Status: {self.booking_status}"


# ===== Signal: Update Seat Status on Booking =====
@receiver(post_save, sender=Booking)
def change_seat_status_when_booked(sender, instance, **kwargs):
    """
    Signal to update the seat status and assign a schedule when a booking is created or updated.
    """
#     # Assign the schedule based on the bus
#     if instance.bus_reserve:
#         commission_obj = Commission.objects.create(
# #             bus_reserve=instance,
# #             commission_type='bus_reservation',
# #             total_earnings=instance.price,
# #             total_commission=Decimal(0)
    if instance.bus:
        try:
            schedule = Schedule.objects.get(bus=instance.bus)
            instance.schedule = schedule
            instance.__class__.objects.filter(pk=instance.pk).update(schedule=schedule)
        except Schedule.DoesNotExist:
            print(f"Schedule not found for bus: {instance.bus}")

        # # Update seat status based on booking status
        # if instance.booking_status in ['booked', 'pending']:
        #     instance.seat.status = 'booked'
        #     instance.seat.save()

        #     # Schedule Celery task to release unpaid seat after 10 minutes
        #     # release_unpaid_seat.apply_async((instance.id,), countdown=600)
        # else:
        #     instance.seat.status = 'available'
        #     instance.seat.save()




# ======== Bus Reservatiom Booking ==========
class BusReservationBooking(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('available', 'Available')
    )
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.CASCADE)
    bus_reserve=models.ForeignKey('bus.BusReservation',on_delete=models.CASCADE)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="booked")
    source=models.CharField(max_length=100)
    destination=models.CharField(max_length=100)
    start_date=models.DateField()
    date=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    

# Signal to create a commission entry when a BusReservationBooking is created
@receiver(post_save, sender=BusReservationBooking)
def create_commission_on_reservation(sender, instance, created, **kwargs):
    """
    Creates a commission entry when a BusReservation is created.
    """
    if created  and instance.status=='booked':
        
        commission_obj = Commission.objects.create(
            bus_reserve=instance.bus_reserve,
            commission_type='bus_reservation',
            total_earnings=instance.bus_reserve.price,
            total_commission=Decimal(0)
        )
        commission_obj.total_commission = commission_obj.calculate_commission(instance.bus_reserve.price)
        commission_obj.save()
        
        
# ===== Rate Model =====
class Rate(models.Model):
    """
    Represents the commission rate for the system.
    """
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Rate for commission"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['rate'], name='unique_rate')
        ]

    def save(self, *args, **kwargs):
        if Rate.objects.exists() and not self.pk:
            raise ValidationError("There can only be one rate entry.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Commission Rate: {self.rate}%"


# ===== Payment Model =====
class Payment(models.Model):
    """
    Represents a payment made by a user for a booking.
    """
    METHODS_CHOICES=(
        ('khalti','Khalti'),
        ('esewa','Esewa')
        
    )
   
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of paid")
    payment_method=models.CharField(max_length=20,choices=METHODS_CHOICES,null=True,blank=True)
    commission_deducted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Commission deducted from payment"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Payment in  {self.payment_method} for Rs {self.price} "


# ===== Commission Model =====
class Commission(models.Model):
    """
    Represents the commission earned by the system for a bus or bus reservation.
    """
    STATUS_CHOICES = (
        ('bus', 'Bus'),
        ('bus_reservation', 'Bus Reservation')
    )

    bus = models.ForeignKey(
        'bus.Bus',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Bus associated with commission"
    )
    bus_reserve = models.ForeignKey(
        'bus.BusReservation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Bus reservation associated with commission"
    )
    commission_type = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='bus',
        help_text="Type of commission"
    )
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total earnings of one bus"
    )
    total_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total commission deducted"
    )

    def calculate_commission(self, earning):
        """
        Calculate commission based on the earning.
        """
        rate = Rate.objects.first()
        if rate:
            return (rate.rate / 100) * earning
        return Decimal(0)

    def __str__(self):
        return f"Commission for {self.bus.bus_number}"


# ===== BusLayout Model =====
class BusLayout(models.Model):
    """
    Represents the seating layout of a bus.
    """
    bus = models.OneToOneField(
        'bus.Bus',
        on_delete=models.CASCADE,
        related_name='layout',  # Add a unique related_name to avoid reverse query name clash
        help_text="Bus associated with this layout",
        null=True,
        blank=True
        
    )
    rows = models.PositiveIntegerField()
    column = models.PositiveIntegerField()
    aisle_column = models.PositiveIntegerField()
    layout_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bus} ({self.created_at})"

    class Meta:
        ordering = ['-created_at']


# ===== Helper: Prevent Recursion in Signals =====
def is_post_save_signal(instance):
    """
    Helper function to prevent recursion in signals.
    """
    return hasattr(instance, '_is_post_save_signal')


# ===== Signal: Update Booking and Calculate Commission on Payment =====
@receiver(post_save, sender=Payment)
def update_status_booking_and_calculate_commission_on_payment(sender, instance, created, **kwargs):
    """
    Signal to update booking status and calculate commission when a payment is saved.
    """
    # Update booking status to 'booked' if payment is made
    if created and instance.price > 0:
        try:
            booking = Booking.objects.get(
                user=instance.user,
                bus=instance.schedule.bus,
                booking_status='pending'
            )
          
            booking.booking_status = 'booked'
            booking.save()
        except Booking.DoesNotExist:
            pass

    # Calculate commission for the payment
    if is_post_save_signal(instance):
        return

    instance._is_post_save_signal = True

    try:
        rate = Rate.objects.first()
        if rate:
            commission, created = Commission.objects.get_or_create(bus=instance.schedule.bus)
            price = Decimal(instance.price)

            # Calculate the commission amount
            commission_amount = Decimal(commission.calculate_commission(price))

            # Update commission and earnings
            commission.total_commission +=commission_amount
            commission.total_earnings += price

            # Update payment with deducted commission
            instance.commission_deducted = commission_amount
            commission.save()
            instance.save(update_fields=['commission_deducted'])
    finally:
        del instance._is_post_save_signal