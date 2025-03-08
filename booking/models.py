from django.db import models
from bus.models import Bus

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




class Seat(models.Model):
    STATUS_CHOICES=(
        ('available','Available'),
        ('booked','Booked')
    )
    bus=models.ForeignKey('bus.Bus',on_delete=models.CASCADE,related_name='seats')
    row=models.CharField(max_length=1 ,help_text="Row letter (A,B,C)")
    number=models.PositiveIntegerField(help_text="Seat Number (1,2,3)") 
    status=models.CharField(max_length=10,choices=STATUS_CHOICES,default="available")
    
    class Meta:
        unique_together=('bus','row','number')
    
    def __str__(self):
        return f"Bus: {self.bus.bus_number} | Row: {self.row} | Seat: {self.number} | Status: {self.status}"
        
    

class Booking(models.Model):
    STATUS_CHOICES=(
    ('pending','Pending'),
    ('booked','Booked'),
    ('canceled','Canceled')
    )
    user=models.ForeignKey('custom_user.CustomUser',on_delete=models.CASCADE,limit_choices_to={'role':'customer'})
    seat=models.ForeignKey(Seat,on_delete=models.CASCADE)
    bus=models.ForeignKey(Bus,on_delete=models.CASCADE,related_name='booking')
    schedule=models.ForeignKey('route.Schedule',on_delete=models.CASCADE)
    booking_status=models.CharField(max_length=25,choices=STATUS_CHOICES,default='pending')
    booked_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateField(auto_now=True)
    