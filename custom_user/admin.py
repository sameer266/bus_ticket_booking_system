from django.contrib import admin

# Register your models here.
from django.contrib import admin
from custom_user.models import CustomUser

from bus.models import Bus,BusAdmin,Driver,Staff,TicketCounter
from booking.models import Booking,Seat
from route.models import Route,Schedule 

# Registering CustomUser model
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
        ('Personal info', {'fields': ('full_name', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)


# ===== Tickert Counter ========
class TicketCounterAdmin(admin.ModelAdmin):
    list_display=('user','counter_name','location')
    
admin.site.register(TicketCounter,TicketCounterAdmin)
    


# Registering BusAdmin model
class BusAdminAdmin(admin.ModelAdmin):
    list_display = ('user','bus')
  
  

admin.site.register(BusAdmin, BusAdminAdmin)

# Registering Driver model
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number')
    search_fields = ('full_name', 'phone_number')

admin.site.register(Driver, DriverAdmin)

# Registering Staff model
class StaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number')
    search_fields = ('full_name', 'phone_number')

admin.site.register(Staff, StaffAdmin)

# Registering Bus model
class BusAdminModel(admin.ModelAdmin):
    list_display = ('bus_number', 'bus_type', 'total_seats', 'available_seats', 'route', 'is_active')
    search_fields = ('bus_number', 'bus_type')
    list_filter = ('is_active',)

admin.site.register(Bus, BusAdminModel)

# Registering Seat model
class SeatAdmin(admin.ModelAdmin):
    list_display = ('bus', 'row', 'number', 'status')
    search_fields = ('bus__bus_number', 'row', 'number')
    list_filter = ('status',)

admin.site.register(Seat, SeatAdmin)

# Registering Booking model
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'bus','schedule','booking_status', 'booked_at', 'updated_at')
    search_fields = ('user__email', 'seat__row', 'seat__number', 'bus__bus_number')
    list_filter = ('booking_status' ,'booked_at',)

admin.site.register(Booking, BookingAdmin)


class RouteAdmin(admin.ModelAdmin):
    list_display = ('source', 'destination', 'distance', 'estimated_time')  # Display these fields in the admin list view
    search_fields = ('source', 'destination')  # Allow searching by source and destination
    list_filter = ('source', 'destination')  # Filter by source and destination
    ordering = ('source',)  # Ordering by source

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('bus', 'route', 'departure_time', 'arrival_time', 'date', 'price','bus_admin')  # Display fields for schedule
    search_fields = ('bus__bus_number', 'route__source', 'route__destination')  # Search schedules by bus number, source, and destination
    list_filter = ('route', 'departure_time', 'date')  # Allow filtering by route and departure time
    ordering = ('date',)  # Ordering by date of journey

# Register the models with the admin site
admin.site.register(Route, RouteAdmin)
admin.site.register(Schedule, ScheduleAdmin)
