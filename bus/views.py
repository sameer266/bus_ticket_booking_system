from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BusAdmin, Bus, Schedule,BusReservation
from booking.models import Booking,BusReservationBooking,Payment,Commission



from django.core.paginator import EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect

@login_required
def bus_admin_dashboard(request):
    # Get the current user
    user = request.user
    
    # Fetch the BusAdmin instance for the user, handle case where it might not exist
    bus_admin = get_object_or_404(BusAdmin, user=user)
    admin_buses = bus_admin.bus
    
    # Fetch the first schedule to get route information (assuming one bus has one primary route)
    schedule = Schedule.objects.filter(bus=admin_buses).first()
    route = schedule.route if schedule else None
    
    # Get bookings for the admin's bus
    admin_bookings = Booking.objects.filter(bus=admin_buses)
    total_bookings = admin_bookings.count()
    recent_bookings = admin_bookings.order_by('-booked_at')[:5]  # Get 5 most recent bookings

    context = {
        'bus': admin_buses,
        'route': route,
        'total_bookings': total_bookings,
        'recent_bookings': recent_bookings,
        'page_title': 'Bus Admin Dashboard'
    }
    
    return render(request, 'bus_admin/dashboard.html', context)

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from decimal import Decimal
from django.utils.dateparse import parse_date



@login_required
def bus_admin_profile(request):
    # Get the current user
    user = request.user
    
    # Fetch the BusAdmin instance for the user
    bus_admin = get_object_or_404(BusAdmin, user=user)
    bus = bus_admin.bus if bus_admin.bus else None

    context = {
        'user': user,
        'bus_admin': bus_admin,
        'bus': bus,
    }
    
    return render(request, 'bus_admin/profile.html', context)



@login_required
def schedule_list(request):
        try:
            # Get the current user and bus_admin
            user = request.user
            bus_admin = get_object_or_404(BusAdmin, user=user)
            admin_bus = bus_admin.bus

            # Update all schedule statuses
            Schedule.update_all_status()

            # Filter schedules for the admin's bus
            schedules = Schedule.objects.filter(bus=admin_bus).order_by('-departure_time')

            # Handle search and filtering
            selected_date_str = request.GET.get('date')
            search_query = request.GET.get('search', '').strip()
            time_range = request.GET.get('time_range', '').strip()

            # Apply date filter if provided
            if selected_date_str:
                try:
                    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                    schedules = schedules.filter(departure_time__date=selected_date)
                except ValueError:
                    selected_date = None
                    messages.warning(request, "Invalid date format, showing all schedules")
            else:
                selected_date = None

            # Apply other filters
            if search_query:
                schedules = schedules.filter(
                    Q(route__source__icontains=search_query) |
                    Q(route__destination__icontains=search_query) |
                    Q(price__icontains=search_query)
                )
            if time_range:
                schedules = schedules.filter(status=time_range)

            context = {
                'schedules': schedules,
                'bus': admin_bus,
                'selected_date': selected_date.isoformat() if selected_date else '',
                'search_query': search_query,
                'time_range': time_range,
            }
            
            return render(request, "admin/manage_schedule.html", context)

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('bus_admin_dashboard')

def booking_management(request):
    try:
        # Get the current user and bus_admin
        user = request.user
        bus_admin = get_object_or_404(BusAdmin, user=user)
        admin_bus = bus_admin.bus

        # Get bookings for the admin's bus
        booking_data = Booking.objects.filter(bus=admin_bus).order_by('-booked_at')
                        
        booking_paginator = Paginator(booking_data, 10) 
        page_number_booking = request.GET.get('page')
        booking_page = booking_paginator.get_page(page_number_booking)

        return render(request, 'bus_admin/booking.html', {
                        'booking_data': booking_page,
                    })
    except Exception as e:
        return render(request, 'bus_admin/booking.html', {'error': str(e)})
                
                
@login_required 
def bus_payment_details(request):
                        # Check if user is a bus_admin
                        if not request.user.role == 'bus_admin':
                            messages.error(request, "Unauthorized access")
                            return redirect('home')

                        user = request.user
                        # Get the bus admin instance
                        bus_admin = get_object_or_404(BusAdmin, user=user)
                        admin_bus = bus_admin.bus

                        # Filter payments only for admin's bus
                        payments_query = Payment.objects.filter(
                            booking__bus=admin_bus,
                            payment_status='completed'
                        ).order_by('-created_at')

                        date_filter = request.GET.get('date_filter', 'all')
                        if date_filter != 'all':
                            today = timezone.now().date()
                            if date_filter == 'today':
                                payments_query = payments_query.filter(created_at__date=today)
                            elif date_filter == 'week':
                                start_of_week = today - timezone.timedelta(days=today.weekday())
                                payments_query = payments_query.filter(created_at__date__gte=start_of_week)
                            elif date_filter == 'month':
                                payments_query = payments_query.filter(created_at__month=today.month, created_at__year=today.year)
                            elif date_filter == 'year':
                                payments_query = payments_query.filter(created_at__year=today.year)

                        # Paginate payments
                        payments_per_page = 10
                        payment_paginator = Paginator(payments_query or [], payments_per_page)
                        page = request.GET.get('payment_page')
                        
                        try:
                            payments = payment_paginator.page(page)
                        except PageNotAnInteger:
                            payments = payment_paginator.page(1)
                        except EmptyPage:
                            payments = payment_paginator.page(payment_paginator.num_pages)

                        # Calculate earnings for admin's bus
                        commission = Commission.objects.filter(bus=admin_bus).first()
                        commission_rate = commission.rate if commission else Decimal('0.00')

                        # Calculate total earnings
                        total_earning = payments_query.aggregate(
                            total=Sum('booking__schedule__price')
                        )['total'] or Decimal('0.00')
                        
                        # Calculate commission and net earnings
                        total_commission = (total_earning * commission_rate / 100) if commission_rate else Decimal('0.00')
                        net_earning = total_earning - total_commission
                        
                        # Count completed trips
                        total_trips = Schedule.objects.filter(
                            bus=admin_bus, 
                            status="finished"
                        ).count()

                        bus_earnings = [{
                            'bus': admin_bus,
                            'rate': float(commission_rate),
                            'bus_number': admin_bus.bus_number,
                            'bus_type': admin_bus.bus_type,
                            'total_earning': float(total_earning),
                            'total_commission': float(total_commission),
                            'net_earning': float(net_earning),
                            'total_trips': total_trips
                        }]

                        # Get today's completed payments
                        today = timezone.now().date()
                        today_payments = Payment.objects.filter(
                            payment_status="completed",
                            created_at__date=today,
                            booking__bus=admin_bus
                        ).order_by('-created_at')
                        
                        today_paginator = Paginator(today_payments or [], 10)
                        today_page = request.GET.get('today_page')
                        
                        try:
                            paginated_today_payments = today_paginator.page(today_page)
                        except PageNotAnInteger:
                            paginated_today_payments = today_paginator.page(1)
                        except EmptyPage:
                            paginated_today_payments = today_paginator.page(today_paginator.num_pages)

                        context = {
                            'payments': paginated_today_payments,
                            'bus_earnings': bus_earnings,
                            'total_amount': float(total_earning),
                            'total_commission': float(total_commission),
                            'total_received': float(net_earning),
                            'date_filter': date_filter,
                        }

                        return render(request, 'admin/bus_payment_details.html', context)




@login_required
def payment_list(request):
    """
    Display paginated list of all payments with filtering options
    """


    
    user = request.user
    bus_admin = get_object_or_404(BusAdmin, user=user)
    admin_bus = bus_admin.bus
    
    # Base queryset with proper joins
    payments = Payment.objects.select_related(
        'user', 
        'booking', 
        'booking__bus'
    ).filter(booking__bus=admin_bus).order_by('-created_at')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    payment_method = request.GET.get('payment_method')
    payment_status = request.GET.get('payment_status')
    search_query = request.GET.get('search')
    
    if start_date:
        start_date_parsed = parse_date(start_date)
        if start_date_parsed:
            payments = payments.filter(created_at__date__gte=start_date_parsed)
    
    if end_date:
        end_date_parsed = parse_date(end_date)
        if end_date_parsed:
            payments = payments.filter(created_at__date__lte=end_date_parsed)
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    if payment_status:
        payments = payments.filter(payment_status=payment_status)
    
    if search_query:
        payments = payments.filter(
            Q(transaction_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(booking__bus__bus_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(payments, 20)  # Show 20 payments per page
    page = request.GET.get('page')
    
    try:
        payments_page = paginator.page(page)
    except PageNotAnInteger:
        payments_page = paginator.page(1)
    except EmptyPage:
        payments_page = paginator.page(paginator.num_pages)
    
    context = {
        'payments': payments_page,
        'start_date': start_date,
        'end_date': end_date,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'search_query': search_query,
        'payment_methods': Payment.METHODS_CHOICES,
        'payment_statuses': Payment.STATUS_CHOICES,
        'page_obj': payments_page,
        'is_paginated': payments_page.has_other_pages(),
    }
    
    return render(request, 'admin/payments/payment_list.html', context)

