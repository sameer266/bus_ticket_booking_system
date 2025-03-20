from  .models import Route,Schedule,Trip,CustomerReview
from custom_user.models import CustomUser
from bus.models import Bus,TicketCounter,Driver,Staff,BusReservation
from rest_framework import serializers
from booking.models import Booking,Seat,Payment,Commission,Rate




class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Route
        fields=['id','source','destination','distance','estimated_time']
    
    
    

class BusScheduleSerializer(serializers.ModelSerializer):
   
    route=RouteSerializer()
    class Meta:
        model=Bus
        fields=['id','bus_number','bus_type','total_seats','available_seats','features','bus_image','route']
        

class ScheduleSerializer(serializers.ModelSerializer):
    bus=BusScheduleSerializer()
    route=RouteSerializer()
    
    class Meta:
        model=Schedule
        fields='__all__'

class TripSerilaizer(serializers.ModelSerializer):
    class Meta:
        model=Trip
        fields='__all__'
        

class CustomUserReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['full_name','phone','email','gender']


class BusReservationSerializer(serializers.ModelSerializer):
    bus=BusScheduleSerializer()
    user=CustomUserReviewSerializer()
    class Meta:
        model=BusReservation
        fields=['id','bus','user','reservation_date','status']


class CustomReviewSerializer(serializers.ModelSerializer):
    bus=BusScheduleSerializer()
    user=CustomUserReviewSerializer()
    route=RouteSerializer()
    
    class Meta:
        model=CustomerReview
        fields='__all__'


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model=Seat
        fields="__all__"
        
        
class BookingSerializer(serializers.ModelSerializer):
    schedule=ScheduleSerializer()
    user=CustomUserReviewSerializer()
    seat=SeatSerializer()
    
    class Meta:
        model=Booking
        fields='__all__'
        
        



# ======== Admin Dashboard ===========
class TicketCounterSerializer(serializers.ModelSerializer):
    user=CustomUserReviewSerializer()
    class Meta:
       model=TicketCounter
       fields='__all__'
       
class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model=Driver
        fields='__all__'

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model=Staff
        fields='__all__'
       
class BusSerializer(serializers.ModelSerializer):
    staff=StaffSerializer()
    driver=DriverSerializer()
    route=RouteSerializer()
   
    class Meta:
        model=Bus
        fields='__all__'


class PaymentSerilaizer(serializers.ModelSerializer):
    user=CustomUserReviewSerializer()
    schedule=ScheduleSerializer()
    class Meta:
        model=Payment
        fields='__all__'
        
class CommissionSerilaizer(serializers.ModelSerializer):
    bus=BusScheduleSerializer()
    
    class Meta:
        model=Commission
        fields='__all__'

class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Rate
        fields='__all__'