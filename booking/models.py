from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.apps import apps

from decimal import Decimal
from bus.models import Bus
from route.models import Schedule
from .tasks import release_unpaid_seat


# ===== Booking Model =====
class Booking(models.Model):
    """
    Represents a booking made by a user for a specific seat on a bus.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('booked', 'Booked'),
        ('canceled', 'Canceled')
    )

    user = models.ForeignKey(
        'custom_user.CustomUser',
        on_delete=models.SET_NULL,null=True,
        limit_choices_to={'role': 'customer'}
    )
    
    seat = models.JSONField(default=list)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='booking',null=True,blank=True)
    schedule = models.ForeignKey(
        'route.Schedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    boarding_point=models.CharField(max_length=200,null=True,blank=True)
    ticket_id=models.CharField(max_length=100,null=True,blank=True)
    booking_status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    booked_at = models.DateTimeField(auto_now_add=True)
    
    def generate_ticket_id(self):
        """Generate a unique ticket ID"""
        if self.schedule and self.bus:
            source_letter = self.schedule.route.source[0].upper()
            dest_letter = self.schedule.route.destination[0].upper()
            bus_last_digits = str(self.bus.bus_number)[-2:] if self.bus.bus_number else "00"
            booking_id = str(self.id)
            return f"TCK-{source_letter}{dest_letter}-{bus_last_digits}-{booking_id}"
        return None


    def save(self,*args,**kwargs):
        if not self.ticket_id:
            self.ticket_id = self.generate_ticket_id()
        super().save(*args,**kwargs)

    def __str__(self):
        return f"Booking #{self.id} - Seat: {self.seat} - Status: {self.booking_status}"


# ===== Signal: Update Seat Status on Booking =====
@receiver(post_save, sender=Booking)
def change_seat_status_when_booked(sender, instance, **kwargs):
    """
    Signal to update the seat status and assign a schedule when a booking is created or updated.
    """
    
    # # Update seat statuses based on booking status
    # if instance.booking_status == "booked":
      
    #             try:
    #                 bus_layout = SeatLayoutBooking.objects.get(schedule=instance.schedule)
    #                 bus_layout.mark_seat_booked(instance.seat)
                    
    #             except SeatLayoutBooking.DoesNotExist:
    #                 pass
           
    # elif instance.booking_status == "canceled":
       

    #             try:
    #                 bus_layout = SeatLayoutBooking.objects.get(schedule=instance.schedule)
    #                 bus_layout.mark_seat_available(instance.seat)
                    
    #             except SeatLayoutBooking.DoesNotExist:
    #                 pass
           
    # elif instance.booking_status == "pending":
     
    #             try:
    #                 bus_layout = SeatLayoutBooking.objects.get(schedule=instance.schedule)
    #                 bus_layout.mark_seat_booked(instance.seat)
    #             except SeatLayoutBooking.DoesNotExist:
    #                 pass
                
                # Schedule task to release seat after 15 minutes if payment not completed
                
                
    if instance.booking_status == "pending":
        try:
            print("------------")
            release_unpaid_seat.apply_async(
                        args=[instance.id, instance.schedule.id],
                        countdown=300
                    )
        except Exception as e:
            print("Error in redis " ,e)
            pass


# ======== Bus Reservatiom Booking ==========
class BusReservationBooking(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('pending', 'Pending')
    )
    
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.SET_NULL,null=True)
    bus_reserve=models.ForeignKey('bus.BusReservation',on_delete=models.SET_NULL,null=True,related_name="reservation_booking")
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")
    source=models.CharField(max_length=100)
    destination=models.CharField(max_length=100)
    start_date=models.DateField()
    end_date=models.DateField(null= True,blank=True)
    date=models.PositiveIntegerField(default=0)
    agreed_price=models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    created_at=models.DateTimeField(auto_now_add=True)
    
  


# Signal to create a commission entry when a BusReservationBooking is created
@receiver(post_save, sender=BusReservationBooking)
def create_commission_on_reservation(sender, instance, created, **kwargs):
    """
    Creates a commission entry when a BusReservation is created.
    """
    if created  or instance.status=='booked':
      
        commission_obj = Commission.objects.create(
            bus_reserve=instance.bus_reserve,
            commission_type='bus_reservation',
            total_earnings=instance.bus_reserve.price,
            total_commission=Decimal(0)
        )
        commission_obj.total_commission = commission_obj.calculate_commission(instance.bus_reserve.price)
        commission_obj.save()
    
from django.utils.timezone import now
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
   
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.SET_NULL,limit_choices_to={'role':'customer'},null=True)
    booking=models.ForeignKey(Booking,on_delete=models.CASCADE,null=True,blank=True)
    payment_method=models.CharField(max_length=20,choices=METHODS_CHOICES,default="khalti")
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    commission_deducted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Commission deducted from payment"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    

    def generate_transaction_id(self):
        """Generate a unique transaction ID"""
        if self.booking and self.booking.schedule and self.booking.bus:
            timestamp = now().strftime('%Y%m%d%H%M')
            schedule_id = str(self.booking.schedule.id).zfill(4)
            bus_id = str(self.booking.bus.id).zfill(4)
            user_id = str(self.user.id).zfill(4)
            return f"TXN--{timestamp}-S{schedule_id}-B{bus_id}-U{user_id}"
        return None

    
    def save(self,*args,**kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
            
        if self.payment_status=="completed":
            commission = Commission.objects.get(bus=self.booking.bus)
            self.commission_deducted = (commission.rate / Decimal('100.00')) * self.booking.schedule.price

        super().save(*args,**kwargs)
            
    def __str__(self):
        return f"Payment #{self.id} - {self.booking.schedule.price} - {self.payment_status}"


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
    Signal to update booking status and calculate commission when a payment is completed.
    """
    if not created:
        return  

    if instance.payment_status != 'completed':
        return 

    try:
        booking = instance.booking  # Assuming a direct FK to Booking
        schedule = booking.schedule

        # Update booking status if pending
        if booking.booking_status == 'pending':
            booking.booking_status = 'booked'
            booking.save()
            print(f"Booking status updated for Booking ID: {booking.id}")

        try:
            commission = Commission.objects.get(bus=schedule.bus)
            rate = commission.rate  
            price = schedule.price
            commission_amount = (price * rate) / Decimal('100.00')
            
            # Update commission details
            commission.total_earnings = price
            commission.total_commission = commission_amount
            commission.save()
            
            # Update payment with commission
            instance.__class__.objects.filter(pk=instance.pk).update(
                commission_deducted=commission_amount
            )
            print(f"Commission calculated and saved: {commission_amount}")

        except Commission.DoesNotExist:
            print(f"No commission setup for bus {schedule.bus}")
        except Exception as e:
            print(f"Error calculating commission: {e}")

    except Exception as e:
        print(f"Error processing payment signal: {e}")
        
        
        
# ===== Commission Model =====
class Commission(models.Model):
    """
    Represents the commission earned by the system for a bus or bus reservation.
    """
    STATUS_CHOICES = (
        ('bus', 'Bus'),
        ('bus_reservation', 'Bus Reservation')
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Rate for commission"
    )
    agent=models.ForeignKey('custom_user.Agent',on_delete=models.SET_NULL,null=True)
    bus = models.ForeignKey(
        'bus.Bus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commission",
        help_text="Bus associated with commission"
    )
    transportation_company=models.ForeignKey('custom_user.TransportationCompany',on_delete=models.SET_NULL,null=True,related_name="transportation_company_commission")
    schedule=models.ForeignKey(Schedule,on_delete=models.SET_NULL,null=True,blank=True)
    bus_reserve = models.ForeignKey(
        'bus.BusReservation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vehicle_commission',
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
    created_at=models.DateTimeField(auto_now_add=True,null=True)

    def calculate_commission(self, earning):
        """
        Calculate commission based on the earning.
        """
        
        if self.rate:
            earning= Decimal(str(earning))
            return (self.rate / Decimal(100)) * earning
        return Decimal(0)

    def __str__(self):
        commission_type_str = "Bus" if self.bus else "Bus Reservation"
        amount = self.total_commission
        return f"Commission for {commission_type_str}: {amount}"

