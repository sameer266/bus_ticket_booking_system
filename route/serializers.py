from  .models import Route,Schedule,Trip
from bus.models import Bus
from rest_framework import serializers


class BusScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model=Bus
        fields=['bus_type','total_seats','available_seats',]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Route
        fields=['source','destination','distance','estimated_time']
    
    
        
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
        
    
        
        
    