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

# # ===== Seat Model =====
# class Seat(models.Model):
#     """
#     Represents a seat in a bus.
#     """
#     STATUS_CHOICES = (
#         ('available', 'Available'),
#         ('booked', 'Booked')
#     )

#     bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE, help_text="Bus to which the seat belongs",
#                             null=True,blank=True)  # Add this field
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="booked")
#     seat_number = models.CharField(max_length=10, help_text="Seat number in the format 'A1'")
    
  
#     class Meta:
#         unique_together = ('seat_number', 'bus')  # Ensure unique seat numbers per bus

#     def __str__(self):
#         return f"Seat: {self.seat_number} | Status: {self.status}"
    
    

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
    payment=models.ForeignKey('booking.Payment',on_delete=models.CASCADE,null=True,blank=True)
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
    if instance.bus:
        try:
            schedule = Schedule.objects.get(bus=instance.bus)
            instance.schedule = schedule
            instance.__class__.objects.filter(pk=instance.pk).update(schedule=schedule)
        except Schedule.DoesNotExist:
            print(f"Schedule not found for bus: {instance.bus}")
    
    # Update seat statuses based on booking status
    if instance.booking_status == "booked":
       for seat_id in instance.seat:
                try:
                    bus_layout = BusLayout.objects.get(bus=instance.bus)
                    bus_layout.update_seat_status(seat_id, 'booked')
                except BusLayout.DoesNotExist:
                    pass
           
    elif instance.booking_status == "canceled":
        for seat_id in instance.seat:

                try:
                    bus_layout = BusLayout.objects.get(bus=instance.bus)
                    bus_layout.update_seat_status(seat_id, 'available')
                except BusLayout.DoesNotExist:
                    pass
           
    elif instance.booking_status == "pending":
        for seat_id in instance.seat:
                try:
                    bus_layout = BusLayout.objects.get(bus=instance.bus)
                    bus_layout.update_seat_status(seat_id, 'booked')
                except BusLayout.DoesNotExist:
                    pass
                
                # Schedule task to release seat after 15 minutes if payment not completed
                # release_unpaid_seat.apply_async(
                #     args=[instance.id, seat_id],
                #     countdown=900  # 15 minutes
                # )
           


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
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    )
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.CASCADE,limit_choices_to={'role':'customer'},null=True,blank=True)
    bus=models.ForeignKey('bus.Bus',on_delete=models.CASCADE,null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of paid")
    payment_method=models.CharField(max_length=20,choices=METHODS_CHOICES,default="khalti")
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    commission_deducted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Commission deducted from payment"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def __str__(self):
        return f"Payment #{self.id} - {self.price} - {self.payment_status}"


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
    if is_post_save_signal(instance):
        return
    
    # Only process if the payment status is completed
    if instance.payment_status == 'completed':
        try:
            # # Find all pending bookings for this user and bus
            bookings = Booking.objects.filter(
                user=instance.user,
                bus=instance.bus,
                booking_status='pending',
                payment__isnull=True  # Only bookings without a payment
            )
            
            if bookings.exists():
                booking = bookings.order_by('-booked_at').first()
                booking.payment = instance
                booking.booking_status = 'booked'
                booking.save()
                
                # Calculate commission
                try:
                    rate = Rate.objects.first()
                    
                    rate_value = rate.rate
                    
                    commission_amount = (instance.price * rate_value) / Decimal('100.00')
                    
                    # Create or update commission record
                    commission, created = Commission.objects.get_or_create(
                        bus=instance.bus,
                        defaults={
                            'commission_type': 'bus',
                            'total_earnings': instance.price,
                            'total_commission': commission_amount
                        }
                    )
                    
                    if not created:
                        commission.total_earnings += instance.price
                        commission.total_commission += commission_amount
                        commission.save()
                    
                    # Update the payment with commission information
                    instance.commission_deducted = commission_amount
                    instance.__class__.objects.filter(pk=instance.pk).update(
                        commission_deducted=commission_amount
                    )
                    
                except Exception as e:
                    print(f"Error calculating commission: {str(e)}")
            
        except Exception as e:
            print(f"Error updating booking status: {str(e)}")


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
        commission_type_str = "Bus" if self.bus else "Bus Reservation"
        amount = self.total_commission
        return f"Commission for {commission_type_str}: {amount}"


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
    
    def update_seat_status(self, seat_number, status):
        """
        Update the status of a specific seat in the layout.
        
        Args:
            seat_number: The seat number to update (e.g., 'A1')
            status: The new status ('available' or 'booked')
        
        Returns:
            bool: True if the seat was updated, False otherwise
        """
        if not self.layout_data:
            return False
            
        for row_idx, row in enumerate(self.layout_data):
            for seat_idx, seat in enumerate(row):
                if isinstance(seat, dict) and seat.get('seat') == seat_number:
                    self.layout_data[row_idx][seat_idx]['status'] = status
                    self.save()
                    return True
        return False
    
    def get_available_seats(self):
        """
        Get a list of all available seats in the layout.
        
        Returns:
            list: List of available seat numbers
        """
        available_seats = []
        if not self.layout_data:
            return available_seats
            
        for row in self.layout_data:
            for seat in row:
                if isinstance(seat, dict) and seat.get('status') == 'available':
                    available_seats.append(seat.get('seat'))
        return available_seats
    
    def __str__(self):
        return f"Layout for {self.bus} - {self.rows}x{self.column}"
    
    class Meta:
        ordering = ['-created_at']
