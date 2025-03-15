from  .models import Route,Schedule,Trip,CustomerReview
from custom_user.models import CustomUser
from bus.models import Bus,TicketCounter
from rest_framework import serializers
from booking.models import Booking



class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Route
        fields=['source','destination','distance','estimated_time']
    
    
    

class BusScheduleSerializer(serializers.ModelSerializer):
    route=RouteSerializer()
    class Meta:
        model=Bus
        fields=['bus_type','total_seats','available_seats','features','bus_image','route']

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



class CustomReviewSerializer(serializers.ModelSerializer):
    bus=BusScheduleSerializer()
    user=CustomUserReviewSerializer()
    route=RouteSerializer()
    
    class Meta:
        model=CustomerReview
        fields='__all__'
        
    
class BookingSerializer(serializers.ModelSerializer):
    schedule=ScheduleSerializer()
    
    class Meta:
        model=Booking
        fields='__all__'
        



# ======== Admin Dashboard ===========
class TicketCounterSerializer(serializers.ModelSerializer):
    user=CustomUserReviewSerializer()
    class Meta:
       model=TicketCounter
       fields='__all__'
       
class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model=Bus
        fields='__all__'
        