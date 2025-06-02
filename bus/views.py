from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Bus, BusAdmin,SeatLayoutBooking
from  route.models import Route
from  booking.models import Booking,BusReservationBooking


@login_required
def bus_admin_dashboard(request):
    # Get summary statistics for the logged-in bus admin only
    user=request.user
    bus_admin=BusAdmin.objects.get(user=user)
    admin_buses = bus_admin.bus
    total_buses = admin_buses.count()
    
    # Get routes and bookings related to admin's buses
    admin_routes = Route.objects.filter(bus__in=admin_buses)
    admin_bookings = Booking.objects.filter(bus__in=admin_buses)
    
    total_bookings = admin_bookings.count()
    total_routes = admin_routes.count()
    recent_bookings = admin_bookings.order_by('-created_at')[:5]  # Get 5 most recent bookings

    context = {
        'total_bookings': total_bookings,
        'total_buses': total_buses,
        'total_routes': total_routes,
        'recent_bookings': recent_bookings,
        'page_title': 'Admin Dashboard'
    }
    
    return render(request, 'bus_admin/dashboard.html', context)