from django.contrib import admin

# Register your models here.
from django.contrib import admin
from custom_user.models import CustomUser

from bus.models import Bus,BusAdmin,Driver,Staff,TicketCounter
from booking.models import Booking,Seat,Payment,Commission,Rate
from route.models import Route,Schedule,Trip,CustomerReview

# Registering CustomUser model
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'role','phone','gender', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone','gender')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
        ('Personal info', {'fields': ('full_name', 'phone','gender')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)


# ===== Tickert Counter ========
class TicketCounterAdmin(admin.ModelAdmin):
    list_display=('user','counter_name','location')
    
admin.site.register(TicketCounter,TicketCounterAdmin)
    


# ========= Bus Admin ==========
class BusAdminAdmin(admin.ModelAdmin):
    list_display = ('user','bus','driver','booked_seats','remaining_seats','estimated_arrival','price','source','destination','last_updated')

admin.site.register(BusAdmin, BusAdminAdmin)



# ======== Driver =============
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number')
    search_fields = ('full_name', 'phone_number')

admin.site.register(Driver, DriverAdmin)

# ===== Staff  ============
class StaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number')
    search_fields = ('full_name', 'phone_number')

admin.site.register(Staff, StaffAdmin)



# ======== Bus ===========
class BusAdminModel(admin.ModelAdmin):
    list_display = ('bus_number', 'bus_type', 'total_seats', 'available_seats','features', 'route', 'is_active')
    search_fields = ('bus_number', 'bus_type')
    list_filter = ('is_active',)

admin.site.register(Bus, BusAdminModel)

#  ========== Seat ===============
class SeatAdmin(admin.ModelAdmin):
    list_display = ('bus', 'row', 'number', 'status')
    search_fields = ('bus__bus_number', 'row', 'number')
    list_filter = ('status',)

admin.site.register(Seat, SeatAdmin)

# ===== booking =============
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'bus','schedule','booking_status','paid', 'booked_at', 'updated_at')
    search_fields = ('user__email', 'seat__row', 'seat__number', 'bus__bus_number')
    list_filter = ('booking_status' ,'booked_at',)

admin.site.register(Booking, BookingAdmin)


# ======== route =============
class RouteAdmin(admin.ModelAdmin):
    list_display = ('source', 'destination', 'distance', 'estimated_time')  # Display these fields in the admin list view
    search_fields = ('source', 'destination')  # Allow searching by source and destination
    list_filter = ('source', 'destination')  # Filter by source and destination
    ordering = ('source',)  # Ordering by source


# ======= Schedule ===========
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('bus', 'route', 'departure_time', 'arrival_time','date',  'price')  # Display fields for schedule
    search_fields = ('bus__bus_number', 'route__source', 'route__destination')  # Search schedules by bus number, source, and destination
    list_filter = ('route', 'departure_time', 'date')  # Allow filtering by route and departure time
    ordering = ('date',)  # Ordering by date of journey

# Register the models with the admin site
admin.site.register(Route, RouteAdmin)
admin.site.register(Schedule, ScheduleAdmin)


# ======== Trip ===============
class  TripAdmin(admin.ModelAdmin):
    list_display=('bus','route','driver','scheduled_departure','scheduled_arrival','actual_departure','actual_arrival','status')

admin.site.register(Trip,TripAdmin)


# ====== Payment ============
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'price', 'commission_deducted', 'created_at')
    search_fields = ('user__email', 'trip__bus__bus_number', 'trip__route__source', 'trip__route__destination')
    list_filter = ('trip__status', 'created_at')

admin.site.register(Payment, PaymentAdmin)

#========== Rate ========
class RateAdmin(admin.ModelAdmin):
    list_display = ('rate',)
    search_fields = ('rate',)
    list_filter = ('rate',)

admin.site.register(Rate, RateAdmin)

# ===== Commission =========
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('bus', 'total_earnings', 'total_commission')
    search_fields = ('bus__bus_number',)
    list_filter = ('bus__bus_number',)

admin.site.register(Commission, CommissionAdmin)



# ====== CustomerReview ============
@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display=('bus','user','rating','route','comment','created_at')

