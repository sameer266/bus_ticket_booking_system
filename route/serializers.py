# ==========================
# Import Necessary Modules and Models
# ==========================
from .models import Route, Schedule, Trip, CustomerReview
from custom_user.models import CustomUser,TransportationCompany
from bus.models import Bus, TicketCounter, Driver, Staff, BusReservation, BusLayout, VechicleType
from rest_framework import serializers
from booking.models import Booking, Payment, Commission, Rate, BusReservationBooking

# ==========================
# Route and Schedule Serializers
# ==========================

# Serializer for Route model
class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'source', 'image', 'destination', 'distance', 'estimated_time']

# Serializer for Bus model with schedule details
class BusScheduleSerializer(serializers.ModelSerializer):
    route = RouteSerializer()

    class Meta:
        model = Bus
        fields = ['id', 'bus_number', 'bus_type', 'total_seats', 'available_seats', 'features', 'bus_image', 'route']

# Serializer for Schedule model
class ScheduleSerializer(serializers.ModelSerializer):
    bus = BusScheduleSerializer()
    route = RouteSerializer()

    class Meta:
        model = Schedule
        fields = '__all__'

# Serializer for Trip model
class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'

# ==========================
# Bus Layout Serializers
# ==========================

# Serializer for BusLayout model
class BusLayoutSerializer(serializers.ModelSerializer):
    bus = BusScheduleSerializer()

    class Meta:
        model = BusLayout
        fields = ['id', 'bus', 'rows', 'column', 'aisle_column', 'layout_data']

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

# Serializer for BusReservation model
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
        fields = ['id', 'name', 'type', 'image', 'vechicle_number', 'vechicle_model', 'color', 'driver', 'staff', 'total_seats', 'price']

# Serializer for BusReservationBooking model
class VechicleReservationBookingSerializer(serializers.ModelSerializer):
    user = CustomUserReviewSerializer()
    bus_reserve = BusReservationSerializer()

    class Meta:
        model = BusReservationBooking
        fields = '__all__'

# Serializer for user-specific BusReservationBooking
class VechicleUserReservationBookingSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    vechicle_number = serializers.SerializerMethodField()

    class Meta:
        model = BusReservationBooking
        fields = '__all__'

    def get_type_name(self, obj):
        """Extracts 'type.name' from BusReservation"""
        return getattr(obj.bus_reserve.type, "name", None) if obj.bus_reserve else None

    def get_image(self, obj):
        """Extracts image URL from BusReservation"""
        if obj.bus_reserve and obj.bus_reserve.image:
            return obj.bus_reserve.image.url  # Return image URL
        return None  # Return None if no image

    def get_vechicle_number(self, obj):
        """Extracts 'vechicle_number' from BusReservation"""
        return getattr(obj.bus_reserve, "vechicle_number", None) if obj.bus_reserve else None

# ==========================
# Booking and Seat Serializers
# ==========================

# Serializer for Booking model
class BookingSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer()
    user = CustomUserReviewSerializer()

    class Meta:
        model = Booking
        fields = '__all__'

class ScheduleBookingUser(serializers.ModelSerializer):
    class Meta:
        model=Schedule
        fields=['id','departure_time','arrival_time','price']
        
#User view Booking Serializer
class UserBookingSerilaizer(serializers.ModelSerializer):
    schedule=ScheduleBookingUser()
    bus_number=serializers.SerializerMethodField()
    source=serializers.SerializerMethodField()
    destination=serializers.SerializerMethodField()
    bus_image=serializers.SerializerMethodField()
    
    class Meta:
        model=Booking
        fields=['seat','bus_number','source','schedule','destination','bus_image','booking_status','booked_at']
     
    def get_bus_number(self,obj):
        return getattr(obj.bus ,"bus_number",None) if obj.bus else None
    
    def get_source(self,obj):
        return getattr(obj.bus.route,'source')
    
    def get_destination(self,obj):
        return getattr(obj.bus.route,'destination')
    
    def get_bus_image(self,obj):
        if obj.bus.bus_image:
            return obj.bus.bus_image.url
        return None

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
class PaymentSerializer(serializers.ModelSerializer):
    user = CustomUserReviewSerializer()
    bus=BusSerializer()

    class Meta:
        model = Payment
        fields = '__all__'

# Serializer for Commission model
class CommissionSerializer(serializers.ModelSerializer):
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


#=======================
# Transportation Compony 
#======================
class TransportationCompanySerializer(serializers.Serializer):
    class Meta:
        model=TransportationCompany
        fileds='__all__'
