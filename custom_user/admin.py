from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from custom_user.models import CustomUser, UserOtp,System,TransportationCompany
from bus.models import Bus,BusFeatures, BusAdmin, Driver, Staff,  BusReservation, BusLayout, VechicleType,SeatLayoutBooking
from booking.models import Booking, Payment, Commission, BusReservationBooking
from route.models import SubRoutes,Route,SearchSubRoute, Schedule, Trip, CustomerReview,Notification

# ========================= Custom User =========================
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'role', 'phone', 'gender', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone', 'gender')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
        ('Personal info', {'fields': ('full_name', 'phone', 'gender')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# ========================= User OTP =========================
class UserOtpAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'otp','temp_name', 'created_at')
    search_fields = ('user__email', 'phone')

admin.site.register(UserOtp, UserOtpAdmin)


# ========================= Bus Admin =========================
class BusAdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'bus', 'driver', 'booked_seats', 'remaining_seats', 'estimated_arrival', 'price', 'source', 'destination', 'last_updated')
    search_fields = ('user__email', 'bus__bus_number', 'source', 'destination')
    list_filter = ('source', 'destination', 'last_updated')

admin.site.register(BusAdmin, BusAdminAdmin)



# ========================= Driver =========================
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'driver_profile', 'license_image')
    search_fields = ('full_name', 'phone_number')

admin.site.register(Driver, DriverAdmin)

# ========================= Staff =========================
class StaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'staff_profile', 'staff_card')
    search_fields = ('full_name', 'phone_number')

admin.site.register(Staff, StaffAdmin)


# ================== Bus Features ==================
class BusFeaturesAdmin(admin.ModelAdmin):
    list_display=('name',)

admin.site.register(BusFeatures,BusFeaturesAdmin)
    
# ========================= Bus =========================
class BusAdminModel(admin.ModelAdmin):
    list_display = ('id', 'driver', 'staff', 'bus_number', 'bus_type', 'bus_image', 'total_seats', 'is_active', 'display_features')
    search_fields = ('bus_number', 'bus_type')

    def display_features(self, obj):
        return ", ".join([feature.name for feature in obj.features.all()])

    display_features.short_description = 'Features'
    

admin.site.register(Bus, BusAdminModel)

# ========================= Vechicle Type =========================
class VechicleTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','image')
    search_fields = ('name',)

admin.site.register(VechicleType, VechicleTypeAdmin)

# ========================= Bus Reservation =========================
class BusReservationAdmin(admin.ModelAdmin):
    list_display = ('id','name','type','image','vechicle_number', 'vechicle_model','color','driver', 'staff', 'total_seats','price','source')
    search_fields = ('vechicle_number', 'user__email', 'driver__full_name', 'staff__full_name')

admin.site.register(BusReservation, BusReservationAdmin)


# =================== Bus Reservation Booking ===================
class BusReservationBookingAdmin(admin.ModelAdmin):
    list_display=('id','user','bus_reserve','status','source','destination','start_date','end_date','date','agreed_price','created_at')

admin.site.register(BusReservationBooking,BusReservationBookingAdmin)
    
    

# ========================= Booking =========================
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'bus', 'schedule', 'booking_status', 'booked_at')
admin.site.register(Booking, BookingAdmin)


# =============== Sub Routes ============
class SubRouteAdmin(admin.ModelAdmin):
    list_display=('id','name')
admin.site.register(SubRoutes,SubRouteAdmin)

# ========================= Route =========================
class RouteAdmin(admin.ModelAdmin):
    list_display = ('id','image','source', 'destination','display_sub_routes', 'distance', 'estimated_time')
    search_fields = ('source', 'destination')
    list_filter = ('source', 'destination')
    ordering = ('source',)
    
    def display_sub_routes(self, obj):
        return ", ".join([sub_route.name for sub_route in obj.sub_routes.all()])

    display_sub_routes.short_description = 'Sub Routes'
    
admin.site.register(Route, RouteAdmin)


# ============= SearchSubRoute =================
class SearchSubRouteAdmin(admin.ModelAdmin):
    list_display=('id','route','subroute','order')

admin.site.register(SearchSubRoute,SearchSubRouteAdmin)

# ========================= Schedule =========================
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id','bus', 'route','available_seats', 'departure_time', 'arrival_time', 'date', 'price')
    search_fields = ('bus__bus_number', 'route__source', 'route__destination')
    list_filter = ('route', 'departure_time', 'date')
    ordering = ('date',)

admin.site.register(Schedule, ScheduleAdmin)

# ========================= Trip =========================
class TripAdmin(admin.ModelAdmin):
    list_display = ('bus', 'route', 'driver', 'scheduled_departure', 'scheduled_arrival', 'actual_departure', 'actual_arrival', 'status')
    search_fields = ('bus__bus_number', 'route__source', 'route__destination', 'driver__full_name')
    list_filter = ('status', 'scheduled_departure', 'scheduled_arrival')

admin.site.register(Trip, TripAdmin)

# ========================= Payment =========================
class PaymentAdmin(admin.ModelAdmin):
    list_display = ( 'user', 'payment_status','payment_method','commission_deducted', 'created_at')
    search_fields = ('user__email', 'schedule__bus__bus_number', 'schedule__route__source', 'schedule__route__destination')
    list_filter = ('created_at',)

admin.site.register(Payment, PaymentAdmin)



# ========================= Commission =========================
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('bus', 'bus_reserve', 'commission_type','rate', 'total_earnings', 'total_commission')
    search_fields = ('bus__bus_number', 'bus_reserve__vechicle_number')
    list_filter = ('commission_type',)

admin.site.register(Commission, CommissionAdmin)

# ========================= Customer Review =========================
@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('bus', 'user', 'rating', 'route', 'comment', 'created_at')
    search_fields = ('bus__bus_number', 'user__email', 'route__source', 'route__destination')
    list_filter = ('rating', 'created_at')

# ========================= Bus Layout =========================
@admin.register(BusLayout)
class BusLayoutAdmin(admin.ModelAdmin):
    list_display = ('bus', 'rows', 'column', 'aisle_column', 'layout_data', 'created_at')
    search_fields = ('bus__bus_number',)
    list_filter = ('created_at',)


# ================ Settings ==========
@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display=('name','phone','image','address','email')
    
#============= Transportation Company =======
@admin.register(TransportationCompany)
class TransportationCompanySerilaizers(admin.ModelAdmin):
    list_display=('company_name','vat_number','location_name','longitude','latitude','bank_name','account_name','account_number','qr_image')
    
# ================= Seat Layout Booking ==========
@admin.register(SeatLayoutBooking)  
class SeatLayoutBookingAdmin(admin.ModelAdmin):
    list_display=('id','layout_data','schedule','created_at')
    
    
# ================= Notification ==========
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display=('id','user','title','message','created_at')
  