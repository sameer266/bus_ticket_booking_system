from django.db import models
from bus.models import Bus
from route.models import Schedule
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals  import post_save
from django.core.exceptions import ValidationError
from decimal import Decimal

# Create your models here.
''' 
{
  "user_id": 123,  // ID of the user booking the seat
  "schedule_id": 456,  // The schedule for the bus trip
  "seat": {
    "row": "A",
    "number": 1
  }
}

'''


# ===== Seat ===========
class Seat(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked')
    )
    
    row = models.CharField(max_length=1, help_text="Row letter (A,B,C)")
    number = models.PositiveIntegerField(help_text="Seat Number (1,2,3)") 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="available")
    
    class Meta:
        unique_together = ( 'row', 'number')
    
    def __str__(self):
        return f"Row: {self.row} | Seat: {self.number} | Status: {self.status}"




# ====== Booking ============
from .tasks import release_unpaid_seat

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('booked', 'Booked'),
        ('canceled', 'Canceled')
    )
    user = models.ForeignKey('custom_user.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'customer'})
    paid = models.BooleanField(default=False)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='booking')
    schedule = models.ForeignKey('route.Schedule', on_delete=models.CASCADE, null=True, blank=True) #Auto created 
    booking_status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    booked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"Booking #{self.id} - Seat: {self.seat} - Status: {self.booking_status}"

# ==== Change the status of seat when booking is booked =======
@receiver(post_save, sender=Booking)
def change_seat_status_when_booked(sender, instance, **kwargs):
    # Assign the schedule based on the bus
    if instance.bus:
        try:
            schedule = Schedule.objects.get(bus=instance.bus)
            
            instance.schedule = schedule
            # Update the instance in the database directly
            instance.__class__.objects.filter(pk=instance.pk).update(schedule=schedule)
        except Schedule.DoesNotExist:
            print(f"Schedule not found for bus: {instance.bus}")

    # Change seat status based on booking status
    if instance.booking_status == 'booked':
        instance.seat.status = 'booked'
        instance.seat.save()
        
    if instance.booking_status == 'pending':
        instance.seat.status = 'booked'
        instance.seat.save()

        # Schedule Celery task to release seat after 10 minutes if unpaid
        # release_unpaid_seat.apply_async((instance.id,), countdown=600)  # 600 seconds = 10 minutes
    else:
        instance.seat.status = 'available'
        instance.seat.save()

    
   

  
  # ======== rate ========
class Rate(models.Model):
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
      
      


# ======== Payment ===========
class Payment(models.Model):
    user = models.ForeignKey('custom_user.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'customer'}, help_text="User who made payment")
    schedule = models.ForeignKey('route.Schedule', on_delete=models.CASCADE, help_text="The Schedule for which the payment was made")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of paid")
    commission_deducted = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Commission deducted from payment")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Payment for {self.schedule.bus.bus_number} for {self.schedule.route.source} - {self.schedule.route.destination}"


# ==== Commission ============

class Commission(models.Model):
    bus = models.ForeignKey('bus.Bus', on_delete=models.CASCADE, help_text="Bus associated with commission")
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total earnings of one bus")
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total commission deducted")
  
    def calculate_commission(self, earning):
        """Calculate commission based on the earning"""
        rate = Rate.objects.first() 
        if rate:
            return (rate.rate / 100) * earning
        return Decimal(0)

    def __str__(self):
        return f"Commission for {self.bus.bus_number}"




# Prevent recursion in signals
def is_post_save_signal(instance):
    return hasattr(instance, '_is_post_save_signal')


# === Signal to Calculate commission when payment is saved ===========
@receiver(post_save, sender=Payment)
def updateStatus_booking_and_calculate_commission_on_payment(sender, instance,created ,**kwargs):
    """  Signals to make booking paid == True if payment  is done """
    if created and instance.price > 0:
      try:    
              booking = Booking.objects.get(
                  user=instance.user, 
                  bus=instance.schedule.bus, 
                  booking_status='pending' 
              )
              print("Booking",booking)
              booking.paid = True
              booking.booking_status = 'booked'
              booking.save()
        
      except:
        pass
            
  
    """ Signals to calculate commission when payment is saved """
    if is_post_save_signal(instance):  # Prevent recursion by checking if signal is already triggered
        return

    instance._is_post_save_signal = True

    try:
        rate = Rate.objects.first()
        if rate:
            commission, created = Commission.objects.get_or_create(bus=instance.schedule.bus)
            if created:
              print(created)
            price = Decimal(instance.price)  
            print(price)

            # Calculate the commission amount
            commission_amount = commission.calculate_commission(price)
            commission_amount = Decimal(commission_amount) 

            commission.total_commission = Decimal(commission.total_commission) + commission_amount
            commission.total_earnings = Decimal(commission.total_earnings) + price

            instance.commission_deducted = commission_amount
            commission.save()
            instance.save(update_fields=['commission_deducted'])

    finally:
        # Ensure that the flag is removed after processing
        del instance._is_post_save_signal