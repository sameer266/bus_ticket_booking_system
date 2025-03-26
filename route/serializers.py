# Import necessary modules and models
from .models import Route, Schedule, Trip, CustomerReview
from custom_user.models import CustomUser
from bus.models import Bus, TicketCounter, Driver, Staff, BusReservation, BusLayout, VechicleType
from rest_framework import serializers
from booking.models import Booking, Seat, Payment, Commission, Rate,BusReservationBooking

# ==========================
# Route and Schedule Serializers
# ==========================

# Serializer for Route model
class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'source','image','destination', 'distance', 'estimated_time']

# Serializer for Bus model with schedule details
class BusScheduleSerializer(serializers.ModelSerializer):
    route = RouteSerializer()

    class Meta:
        model = Bus
        fields = ['id', 'bus_number', 'bus_type', 'total_seats', 'available_seats', 'features', 'bus_image', 'route']

# ==========================
# Bus Layout Serializers
# ==========================

# Serializer for BusLayout model
class BusLayoutSerilizer(serializers.ModelSerializer):
    bus = BusScheduleSerializer()

    class Meta:
        model = BusLayout
        fields = ['id', 'bus', 'rows', 'column', 'aisle_column', 'layout_data']

# ==========================
# Schedule and Trip Serializers
# ==========================

# Serializer for Schedule model
class ScheduleSerializer(serializers.ModelSerializer):
    bus = BusScheduleSerializer()
    route = RouteSerializer()

    class Meta:
        model = Schedule
        fields = '__all__'

# Serializer for Trip model
class TripSerilaizer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'

# ==========================
# User and Review Serializers
# ==========================

# Serializer for CustomUser model
class CustomUserReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone', 'email', 'gender']

# Serializer for CustomerReview model
class CustomReviewSerializer(serializers.ModelSerializer):
    bus = BusScheduleSerializer()
    user = CustomUserReviewSerializer()
    route = RouteSerializer()

    class Meta:
        model = CustomerReview
        fields = '__all__'

# ==========================
# Vehicle and Reservation Serializers
# ==========================

# Serializer for VechicleType model
class VechicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VechicleType
        fields = '__all__'

# =====================
# BusReservation model
# =====================

class TypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = VechicleType
        fields = ['name']

class StaffBusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['full_name']
        
class DriverBusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['full_name']
        
class BusReservationSerializer(serializers.ModelSerializer):
    type = TypesSerializer()
    driver = DriverBusSerializer()
    staff = StaffBusSerializer()

    class Meta:
        model = BusReservation
        fields = ['id','name','type','image', 'vechicle_number','vechicle_model','color','driver', 'staff', 'total_seats', 'price']


class BusReservationBookingSerializer(serializers.ModelSerializer):
    user=CustomUserReviewSerializer()
    class Meta:
        model=BusReservationBooking
        fields='__all__'
        
        
# ==========================
# Booking and Seat Serializers
# ==========================

# Serializer for Seat model
class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = '__all__'

# Serializer for Booking model
class BookingSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer()
    user = CustomUserReviewSerializer()
  

    class Meta:
        model = Booking
        fields = '__all__'

# ==========================
# Admin Dashboard Serializers
# ==========================

# Serializer for TicketCounter model
class TicketCounterSerializer(serializers.ModelSerializer):
    user = CustomUserReviewSerializer()

    class Meta:
        model = TicketCounter
        fields = '__all__'

# Serializer for Driver model
class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'

# Serializer for Staff model
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'

# Serializer for Bus model
class BusSerializer(serializers.ModelSerializer):
    staff = StaffSerializer()
    driver = DriverSerializer()
    route = RouteSerializer()

    class Meta:
        model = Bus
        fields = '__all__'

# ==========================
# Payment and Commission Serializers
# ==========================

# Serializer for Payment model
class PaymentSerilaizer(serializers.ModelSerializer):
    user = CustomUserReviewSerializer()
    

    class Meta:
        model = Payment
        fields = '__all__'

# Serializer for Commission model
class CommissionSerilaizer(serializers.ModelSerializer):
    bus = BusScheduleSerializer()

    class Meta:
        model = Commission
        fields = '__all__'

# ==========================
# Rate Serializer
# ==========================

# Serializer for Rate model
class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = '__all__'