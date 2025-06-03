from django.contrib.auth import authenticate
from django.db.models import Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Count, Sum,F
from datetime import datetime
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

import json


from custom_user.models import CustomUser,System,TransportationCompany
from route.models import SubRoutes, Route,SearchSubRoute, Schedule, Trip,Notification
from bus.models import Bus,BusFeatures,Driver,Staff,BusReservation,BusLayout,VechicleType,SeatLayoutBooking
from booking.models import Commission, Booking,Payment,BusReservationBooking


from route.serializers import (
    BusSerializer,
   
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from datetime import timedelta
from django.utils import timezone

@login_required
def admin_dashboard(request):
    """
    Render the admin dashboard with overview statistics and recent data.
    Shows only company-specific stats if user is sub-admin.
    """
    user = request.user
    user_company = getattr(user, 'transportation_company', None)
    user_role = getattr(user, 'role', 'admin')  # Default to admin if role not set

    data = {}
    chart_data = {}

    # Base querysets
    if user_company:
        # Sub-admin: filter by company
        buses = Bus.objects.filter(transportation_company=user_company, is_active=True)
        commissions = Commission.objects.filter(bus__in=buses)
        bookings = Booking.objects.filter(bus__in=buses)
        trips = Trip.objects.filter(bus__in=buses)
    else:
        # Admin: all data
        buses = Bus.objects.filter(is_active=True)
        commissions = Commission.objects.all()
        bookings = Booking.objects.all()
        trips = Trip.objects.all()

    # Stats
    total_bus_commission = commissions.aggregate(total=Sum('total_commission'))['total'] or 0
    total_reservation_commission = Commission.objects.filter(
        bus_reserve__transportation_company=user_company if user_company else None
    ).aggregate(total=Sum('total_commission'))['total'] or 0
    
    data['total_revenue'] = total_bus_commission + total_reservation_commission
    data['total_active_bus'] = buses.count()
    data['total_user'] = CustomUser.objects.filter(
        role="customer",
        booking__bus__in=buses
    ).distinct().count() if user_company else CustomUser.objects.filter(role="customer").count()
    data['total_booking_pending'] = bookings.filter(booking_status="pending").count()
    data['total_trip_completed'] = trips.filter(status="completed").count()
    data['ticket_booked'] = bookings.filter(booking_status="booked").count()

    # Recent data
    recent_booking = bookings.order_by('-booked_at')[:8]
    trip_data = trips.order_by('-scheduled_departure')[:8]

    # Chart data
    # Revenue over last 7 days
    last_7_days = [timezone.now() - timedelta(days=x) for x in range(6, -1, -1)]
    revenue_data = []
    for day in last_7_days:
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        daily_revenue = commissions.filter(
            created_at__gte=day_start,
            created_at__lt=day_end
        ).aggregate(total=Sum('total_commission'))['total'] or 0
        revenue_data.append(daily_revenue)
    
    chart_data['revenue'] = {
        'labels': [day.strftime('%a') for day in last_7_days],
        'data': [float(x) for x in revenue_data]
    }

    # Booking status
    booking_status = bookings.aggregate(
        booked=Count('id', filter=Q(booking_status='booked')),
        pending=Count('id', filter=Q(booking_status='pending')),
        cancelled=Count('id', filter=Q(booking_status='cancelled'))
    )
    chart_data['booking_status'] = {
        'labels': ['Booked', 'Pending', 'Cancelled'],
        'data': [int(booking_status['booked']), int(booking_status['pending']), int(booking_status['cancelled'])]
    }

    # Top routes (by bookings)
    top_routes = (
        bookings.values('schedule__route__source', 'schedule__route__destination')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    chart_data['routes'] = {
        'labels': [f"{r['schedule__route__source']} to {r['schedule__route__destination']}" for r in top_routes],
        'data': [int(r['count']) for r in top_routes]
    }

    # Monthly trips (last 6 months)
    last_6_months = [(timezone.now() - timedelta(days=30*x)).strftime('%Y-%m') for x in range(5, -1, -1)]
    monthly_trips = []
    for month in last_6_months:
        year, month_num = map(int, month.split('-'))
        month_start = timezone.datetime(year, month_num, 1, tzinfo=timezone.get_current_timezone())
        month_end = (month_start + timedelta(days=31)).replace(day=1)
        trips_count = trips.filter(
            scheduled_departure__gte=month_start,
            scheduled_departure__lt=month_end,
            status='completed'
        ).count()
        monthly_trips.append(int(trips_count))
    
    chart_data['monthly_trips'] = {
        'labels': [month for month in last_6_months],
        'data': monthly_trips
    }

    context = {
        'data': data,
        'recent_booking': recent_booking,
        'trip_data': trip_data,
        'chart_data': json.dumps(chart_data), 
        'user_role': user_role
    }

    return render(request, 'admin/dashboard.html', context)


# ========== Admin dashboard sidebar all views ==============
@login_required
def admin_profile(request):
    if request.method == "POST":
        try:
            user = request.user
            user.full_name = request.POST.get("full_name")
            user.email = request.POST.get("email")
            user.phone = request.POST.get("phone")
            user.gender = request.POST.get("gender")
            user.save()

            messages.success(request, "Profile Updated Successfully")
            return redirect("admin_profile")  # Redirect to avoid form resubmission on refresh
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, "admin/profile.html", {"user": request.user})
        

# ======= Ticket Counter  ===========
@login_required
def transportation_company_list(request):
    if request.method == "POST":
        # Get data from the request
        company_name = request.POST.get('company_name')
        vat_number = request.POST.get('vat_number')
        country = request.POST.get('country')
        location_name = request.POST.get('location_name')
        bank_name = request.POST.get('bank_name')
        account_name = request.POST.get('account_name')
        account_number = request.POST.get('account_number')
        qr_image = request.FILES.get('qr_image')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')

        # Check if user already exists
        if CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, "User with this phone number already exists!")
        else:
            # Create the user
            user = CustomUser.objects.create(
                role='sub_admin',
                full_name=full_name,
                email=email,
                phone=phone,
                gender=gender,
                is_staff=True
            )
            user.set_password("company@123")  # Default Password
            user.save()

            # Create the TransportationCompany
            TransportationCompany.objects.create(
                user=user,
                company_name=company_name,
                vat_number=vat_number,
                country=country,
                location_name=location_name,
              
                
                bank_name=bank_name,
                account_name=account_name,
                account_number=account_number,
                qr_image=qr_image
            )

            messages.success(request, "Transportation Company added successfully!")
            return redirect("transportation_company_list")

    return render(request, "admin/transportation_company.html", {
        "companies": TransportationCompany.objects.all(),
    })
    
@login_required
def edit_transportation_company(request, id):
    transportation_company = get_object_or_404(TransportationCompany, id=id)
    user = transportation_company.user

    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        new_phone = request.POST.get('phone')
        gender = request.POST.get('gender')

       
        if CustomUser.objects.filter(phone=new_phone).exists():
            pass
        
        else:
            user.email=email

        user.full_name = full_name
        user.gender = gender
        user.save()

        # Update TransportationCompany fields
        transportation_company.company_name = request.POST.get('company_name')
        transportation_company.vat_number = request.POST.get('vat_number')
        transportation_company.country = request.POST.get('country')
        transportation_company.location_name = request.POST.get('location_name')
        transportation_company.bank_name = request.POST.get('bank_name')
        transportation_company.account_name = request.POST.get('account_name')
        transportation_company.account_number = request.POST.get('account_number')

        if 'qr_image' in request.FILES:
            transportation_company.qr_image = request.FILES['qr_image']

        transportation_company.save()

        messages.success(request, "Transportation Company updated successfully!")
        return redirect("transportation_company_list")

    return render(request, "admin/edit_transportation_company.html", {
        "transportation_company": transportation_company,
    })


@login_required
def delete_transportation_company(request, id):
    try:
        print(id)
        transportation_company = get_object_or_404(TransportationCompany, id=id)
        user = transportation_company.user
        user.delete()  
        transportation_company.delete()

        messages.success(request, "Ticket Counter deleted successfully!")
        return redirect("transportation_company_list")
    except Exception as e:
        print(str(e))
        return redirect("transportation_company_list")
        
        
        

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# ========= Sub Admin Bus List ==========
@login_required
def sub_admin_bus_list(request, id):
    user = TransportationCompany.objects.filter(id=id).first()

    # Get buses and vehicles
    buses = Bus.objects.filter(transportation_company=user)
    vehicles = BusReservation.objects.filter(transportation_company=user)

    # Get bus schedules and counts
    bus_schedules = Schedule.objects.filter(bus__in=buses).values('id').annotate()
    bus_count = buses.count()
    bus_schedule_count = Schedule.objects.filter(bus__in=buses).count()
    vehicle_count = vehicles.count()

    # Pagination for buses
    bus_paginator = Paginator(buses, 10)
    bus_page = request.GET.get('bus_page')
    try:
        buses_page = bus_paginator.page(bus_page)
    except PageNotAnInteger:
        buses_page = bus_paginator.page(1)
    except EmptyPage:
        buses_page = bus_paginator.page(bus_paginator.num_pages)

    # Pagination for vehicles  
    vehicle_paginator = Paginator(vehicles, 10)
    vehicle_page = request.GET.get('vehicle_page')
    try:
        vehicles_page = vehicle_paginator.page(vehicle_page) 
    except PageNotAnInteger:
        vehicles_page = vehicle_paginator.page(1)
    except EmptyPage:
        vehicles_page = vehicle_paginator.page(vehicle_paginator.num_pages)

    context = {
        'buses': buses_page,
        'vehicles': vehicles_page,
        'bus_schedules': bus_schedules,
        'bus_count': bus_count,
        'bus_schedule_count': bus_schedule_count,
        'vehicle_count': vehicle_count,
    }
    return render(request, 'admin/sub_admin_bus_list.html', context)
            

# ========= User Managemnet ==========
@login_required
def manage_users(request):
    users = CustomUser.objects.filter(role='customer')
    paginator = Paginator(users, 10)  # 10 users per page
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)

    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')

        if CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists")
        else:
            user = CustomUser.objects.create(
                role='customer',
                full_name=full_name,
                email=email,
                phone=phone,
                gender=gender
            )
            user.set_password("counter@123")
            user.save()
        return redirect('manage_users')

    return render(request, 'admin/manage_users.html', {'users': users_page})

@login_required
def delete_user(request, id):
    """Delete a user and refresh the page."""
    user = get_object_or_404(CustomUser, id=id)
    user.delete()
    return redirect('manage_users')



# ======= Driver and staff management ========
@login_required
def manage_driver_and_staff(request):
    """List and add drivers and staff from the same template."""
    
        
    drivers=Driver.objects.none()
    staff=Staff.objects.none()
    transportation_company=getattr(request.user,"transportation_company",None)
    if transportation_company:
        drivers = Driver.objects.filter(transportation_company=transportation_company)
        staff = Staff.objects.filter(transportation_company=transportation_company)
    else:
        drivers = Driver.objects.all()
        staff = Staff.objects.all()

    if request.method == "POST":
        # Handle Driver Add
        if 'add_driver' in request.POST:
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            driver_profile = request.FILES.get('driver_profile')
            license_image = request.FILES.get('license_image')

            if Driver.objects.filter(phone_number=phone_number).exists():
               messages.error(request,"Driver alraedy exists")
            if transportation_company:
                Driver.objects.create(
                    full_name=full_name,
                    phone_number=phone_number,
                    driver_profile=driver_profile,
                    license_image=license_image,
                    transportation_company=transportation_company
                )
            else:
                 Driver.objects.create(
                    full_name=full_name,
                    phone_number=phone_number,
                    driver_profile=driver_profile,
                    license_image=license_image,
                )
                 
            messages.success(request, "Driver added successfully!")
            return redirect('manage_driver_and_staff')  # Reload page after adding driver

        # Handle Staff Add
        elif 'add_staff' in request.POST:
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            staff_profile = request.FILES.get('staff_profile')
            

            if Staff.objects.filter(phone_number=phone_number).exists():
                messages.error(request, "Staff already exists!")
                return redirect('manage_driver_and_staff')
            if transportation_company:
                Staff.objects.create(
                    full_name=full_name,
                    staff_profile=staff_profile,
                    phone_number=phone_number,
                    transportation_company=transportation_company
                )
            else:
                Staff.objects.create(
                    full_name=full_name,
                    staff_profile=staff_profile,
                    phone_number=phone_number,
                    transportation_company=transportation_company
                )
            messages.success(request, "Staff added successfully!")
            return redirect('manage_driver_and_staff')  # Reload page after adding staff

    return render(request, 'admin/managedriver_staff.html', {'drivers': drivers, 'staff': staff})

@login_required
def edit_driver(request, driver_id):
    """Edit an existing driver."""
    driver = get_object_or_404(Driver, id=driver_id)

    if request.method == "POST":
        driver.full_name = request.POST.get('full_name')
        driver.phone_number = request.POST.get('phone_number')
        if 'driver_profile' in request.FILES:
            driver.driver_profile = request.FILES['driver_profile']
        if 'license_image' in request.FILES:
            driver.license_image = request.FILES['license_image']
        driver.save()
        return redirect('manage_driver_and_staff')

    return render(request, 'admin/edit_driver.html', {'driver': driver})


@login_required
def delete_driver(request, driver_id):
    """Delete a driver."""
    driver = get_object_or_404(Driver, id=driver_id)
    driver.delete()
    return redirect('manage_driver_and_staff')


# ======== Edit staff ==========
@login_required
def edit_staff(request, staff_id):
    """Edit an existing staff member."""
    staff = get_object_or_404(Staff, id=staff_id)

    if request.method == "POST":
        staff.full_name = request.POST.get('full_name')
        staff.phone_number = request.POST.get('phone_number')
        if 'staff_profile' in request.FILES:
            staff.staff_profile = request.FILES['staff_profile']
        staff.save()
        return redirect('manage_driver_and_staff')

    return render(request, 'admin/edit_staff.html', {'staff': staff})


# ======== delete Staff ==========
@login_required
def delete_staff(request, staff_id):
    """Delete a staff member."""
    staff = get_object_or_404(Staff, id=staff_id)
    staff.delete()
    return redirect('manage_driver_and_staff')



# =======================
#  BUs Featues 
# ========================
@login_required
def bus_featurelist(request):
    bus_feature = BusFeatures.objects.all()
    return render(request, 'admin/busfeatures/bus_features.html', {'bus_features': bus_feature})



@login_required
def add_bus_feature(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            if BusFeatures.objects.filter(name=name).exists():
                messages.error(request, "Bus feature already exists!")
            else:
                BusFeatures.objects.create(name=name)
                messages.success(request, "Bus feature added successfully!")
                return redirect('busfeature_lists')
    return render(request,'admin/busfeatures/add_bus_feature.html')


@login_required 
def edit_bus_feature(request, feature_id):
    bus_feature = BusFeatures.objects.get(id=feature_id)
    
    if request.method == "POST":
        name = request.POST.get('name')  
        bus_feature.name = name
        bus_feature.save()
        messages.success(request, "Bus feature updated successfully!")
        return redirect('busfeature_lists')
        
    return render(request, 'admin/busfeatures/edit_bus_features.html', {'bus_feature': bus_feature})

@login_required
def delete_bus_feature(request, feature_id):
    bus_feature = get_object_or_404(BusFeatures, id=feature_id)
    bus_feature.delete()
    messages.success(request, "Bus feature deleted successfully!")
    return redirect('busfeature_lists')

# ==================
# Bus Management
# ==================

@login_required
def bus_list(request):
    user = request.user
    company = getattr(user, "transportation_company", None)

    # Get buses, drivers, and staff based on company
    buses = Bus.objects.filter(transportation_company=company) if company else Bus.objects.all()
    drivers = Driver.objects.filter(transportation_company=company) if company else Driver.objects.all()
    staff = Staff.objects.filter(transportation_company=company) if company else Staff.objects.all()

    # === Drivers filtering ===
    assigned_driver_ids = Bus.objects.exclude(driver=None).values_list("driver__id", flat=True)
    scheduled_driver_ids = Schedule.objects.filter(
        departure_time__gte=timezone.now(),
        bus__driver__isnull=False
    ).values_list("bus__driver__id", flat=True)
    

    unassigned_drivers = drivers.exclude(id__in=set(assigned_driver_ids) | set(scheduled_driver_ids))
    print(unassigned_drivers)

    # === Staff filtering ===
    assigned_staff_ids = Bus.objects.exclude(staff=None).values_list("staff__id", flat=True)
    scheduled_staff_ids = Schedule.objects.filter(
        departure_time__gte=timezone.now(),
        bus__staff__isnull=False
    ).values_list("bus__staff__id", flat=True)

    unassigned_staff = staff.exclude(id__in=set(assigned_staff_ids) | set(scheduled_staff_ids))
    transportation_company_list=TransportationCompany.objects.all()
    # === Final context ===
    bus_features=BusFeatures.objects.all()
    context = {
        'buses': buses,
        'transportation_company':transportation_company_list,
        'all_drivers': unassigned_drivers,
        'all_staff': unassigned_staff,
        'bus_types': Bus.VEHICLE_CHOICES,
        'feature_choices':bus_features ,
    }

    return render(request, 'admin/manage_bus.html', context)


# =========== Add Bus =============
@login_required
def create_bus(request):
    print(request.POST)
    transportation_company = getattr(request.user, "transportation_company", None)

    if request.method == "POST":
        try:
            print(request.POST)
            # Extract form data
            bus_number = request.POST.get('bus_number')
            bus_type = request.POST.get('bus_type')
            driver_id = request.POST.get('driver')
            staff_id = request.POST.get('staff')
            transportation_company_id=request.POST.get('transportation')
            if transportation_company_id:
                transportation_company=TransportationCompany.objects.get(id=transportation_company_id)
            
         
            total_seats = int(request.POST.get('total_seats', 0))
            is_active = request.POST.get('is_active') == 'on'

            features = request.POST.getlist('features') 
            features_obj=BusFeatures.objects.filter(name__in=features)
            
            bus_image = request.FILES.get('bus_image')
            layout = request.POST.get('layout')

            driver = Driver.objects.get(id=driver_id) if driver_id else None
            staff = Staff.objects.get(id=staff_id) if staff_id else None
                       
            commission_rate = float(request.POST.get('commission_rate') or 0)
            
            print(total_seats)
            # Create bus
            bus = Bus.objects.create(
                bus_number=bus_number,
                bus_type=bus_type,
                driver=driver,
                staff=staff,
            
            
                total_seats=total_seats,
            
                is_active=is_active,
           
              
                bus_image=bus_image,
                transportation_company=transportation_company
            )
            bus.features.set(features_obj)
           

            if layout:
                layout_data = json.loads(layout)
                BusLayout.objects.create(
                    bus=bus,
                    rows=layout_data['rows'],
                    column=layout_data['columns'],
                    layout_data=layout_data['layout'],
                    aisle_column=layout_data.get('aisleAfterColumn')
                )
   
            Commission.objects.create(bus=bus,rate=commission_rate)

            messages.success(request, "Bus created successfully.")
            return redirect('bus_list')

        except Exception as e:
            messages.error(request, f"Error creating bus: {str(e)}")
            # Fall through to re-render the form with errors

    # GET request or error case
   
    used_driver_ids = Bus.objects.filter(driver__isnull=False).values_list("driver__id", flat=True)
    used_staff_ids = Bus.objects.filter(staff__isnull=False).values_list("staff__id", flat=True)

    drivers = Driver.objects.exclude(id__in=used_driver_ids)
    staff = Staff.objects.exclude(id__in=used_staff_ids)

    if transportation_company:
        drivers = drivers.filter(transportation_company=transportation_company)
        staff = staff.filter(transportation_company=transportation_company)

    bus_features=BusFeatures.objects.all()
    context = {

        'all_drivers': drivers,
        'all_staff': staff,
        'bus_types': Bus.VEHICLE_CHOICES,
        'feature_choices': bus_features,
        'form_data': request.POST if request.method == "POST" else None,  # Preserve form data on error
        'errors': messages.get_messages(request),  # Pass error messages
    }
    return render(request, 'admin/manage_bus.html', context)
    


# ======= Edit bus ===========



@login_required
def edit_bus(request, bus_id):
    print(request.POST)
    bus = get_object_or_404(Bus, id=bus_id)
    
    if request.method == 'POST':
        try:
          
           
            bus.bus_number = request.POST.get('bus_number', bus.bus_number)
            bus.bus_type = request.POST.get('bus_type', bus.bus_type)
            
            # Handle driver
            driver_id = request.POST.get('driver')
            if driver_id:
                bus.driver = Driver.objects.get(id=driver_id) 
            else:
                bus.driver=bus.driver
            
            # Handle staff
            staff_id = request.POST.get('staff')
            if staff_id:
                bus.staff = Staff.objects.get(id=staff_id) 
            else:
                bus.staff=bus.staff
            
            # Get total_seats from layout data if available
            if 'layout' in request.POST:
                layout_data = json.loads(request.POST['layout'])
                total_seats = layout_data.get('totalSeats', bus.total_seats)
                bus.total_seats = int(total_seats)
            else:
                # Fallback to direct input if no layout data
                total_seats = request.POST.get('total_seats', bus.total_seats)
                bus.total_seats = int(total_seats) if total_seats else bus.total_seats
            
            bus.is_active = request.POST.get('is_active') == 'on'
            bus.is_running = request.POST.get('is_running') == 'on'
            
            # Handle features
            features = request.POST.getlist('features')
            if features:
                print("------------bus")
                features_obj = BusFeatures.objects.filter(name__in=features)
                bus.features.set(features_obj)
                
                
            # Handle image
            if 'bus_image' in request.FILES:
                bus.bus_image = request.FILES['bus_image']
            
            
            if 'commission_rate' in request.POST:
                print("------------")
                commission=get_object_or_404(Commission,bus=bus)
                commission.rate=request.POST.get('commission_rate')
                commission.save()
                
            # Validate before saving
            bus.full_clean()
            bus.save()
            
            # Handle layout
            if 'layout' in request.POST:
                layout_data = json.loads(request.POST['layout'])
                bus_layout, created = BusLayout.objects.get_or_create(bus=bus)
                
                bus_layout.rows = layout_data.get('rows', bus_layout.rows)
                bus_layout.column = layout_data.get('columns', bus_layout.column)
                bus_layout.aisle_column = layout_data.get('aisleAfterColumn', bus_layout.aisle_column)
                bus_layout.layout_data = layout_data.get('layout', bus_layout.layout_data)
                bus_layout.full_clean()
                bus_layout.save()
            
            return JsonResponse({
                'success': True,
                'redirect': '/buses-management/',
                'message':'Bus Updated Successfully'
                
            })
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=500)
    


# Add this view to fetch bus data
@login_required
def get_bus(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    try:
        commission = Commission.objects.filter(bus=bus).first()
        rate = commission.rate if commission else 0
    
        layout = BusLayout.objects.get(bus=bus)
        layout_data = {
            'rows': layout.rows,
            'columns': layout.column,  # Ensure this matches your model field
            'aisleAfterColumn': layout.aisle_column,
            'layout': layout.layout_data,
        }
    except BusLayout.DoesNotExist:
        layout_data = {}

    data = {
    'bus_id': bus.id,
    'bus_number': bus.bus_number,
    'bus_type': bus.bus_type,
    'rate': rate,
    'bus_image': bus.bus_image.url if bus.bus_image else '',
    'total_seats': bus.total_seats,
    'driver': bus.driver.id if bus.driver else None,
    'staff': bus.staff.id if bus.staff else None,
    'is_active': bus.is_active,
    'features': [feature.name for feature in bus.features.all()], 
    'layout': json.dumps(layout_data),
    'transportation_company': bus.transportation_company.id if bus.transportation_company else None,
}

    return JsonResponse(data)

@login_required
def delete_bus(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    messages.success(request, f"Bus {bus.bus_number} deleted successfully")
    bus.delete()
    return redirect('bus_list')
    





from django.core.serializers.json import DjangoJSONEncoder
# ======================
# Vehicle Reservation 
# =======================
@login_required
def vehicle_list(request):
    """
    Handles GET (list), POST (create/delete) requests for vehicle reservations.
    """
    user = request.user
    transportation_company = getattr(user, 'transportation_company', None)
    if transportation_company:
        reservations = BusReservation.objects.filter(transportation_company=transportation_company)
    else:
        reservations = BusReservation.objects.all()

    staffs=None
    drivers=None
    if transportation_company:
        staffs = Staff.objects.filter(transportation_company=transportation_company)
        drivers = Driver.objects.filter(transportation_company=transportation_company)
    else:
        staffs = Staff.objects.all()
        drivers = Driver.objects.all()

    vechicle_types = VechicleType.objects.all()
    transportation_company=TransportationCompany.objects.all()

    reservation_json = json.dumps([
        {
            'id': r.id,
            'name': r.name,
            'type_id': r.type_id,
            'vechicle_number': r.vechicle_number,
            'vechicle_model': r.vechicle_model,
            'color': r.color,
            'driver_id': r.driver_id,
            'staff_id': r.staff_id,
            'total_seats': r.total_seats,
            'price': float(r.price) if r.price is not None else None,
        } for r in reservations
    ], cls=DjangoJSONEncoder)
    source=[]
    for i in reservations:
        if i.source not in source:
            source.append(i.source)
            
    context = {
        'reservations': reservations,
        'unassigned_drivers': drivers,
        'unassigned_staff': staffs,
        'vechicle_types': vechicle_types,
        'transportation_company':transportation_company,
        'source':source,
        'reservation_json': reservation_json,
    }

    if request.method == 'POST':
        if 'add_reservation' in request.POST:
            try:
                name = request.POST.get('name')
                type_id = request.POST.get('type')
                transportation_company_id=request.POST.get('transportation_company_id')
                if transportation_company_id:
                    transportation_company_obj=TransportationCompany.objects.get(id=transportation_company_id)

                vechicle_number = request.POST.get('vechicle_number')
                vechicle_model = request.POST.get('vechicle_model')
                image = request.FILES.get('image')
                document = request.FILES.get('document')
                color = request.POST.get('color')
                driver_id = request.POST.get('driver_id')
                staff_id = request.POST.get('staff_id')
                total_seats = request.POST.get('total_seats', 35)
                price = request.POST.get('price')
                source=request.POST.get('source')
                fuel_type=request.POST.get('fuel_type')
                price_range=request.POST.get('price_range')
                
                commission_rate = float(request.POST.get('commission_rate') or 0)
                
                if source:
                    source = source.lower()
                else:
    
                    source = ''  

                type_obj = VechicleType.objects.get(id=type_id) if type_id else None
                driver_obj = Driver.objects.get(id=driver_id) if driver_id else None
                staff_obj = Staff.objects.get(id=staff_id) if staff_id else None

                bus_reserve= BusReservation.objects.create(
                    transportation_company=transportation_company_obj,
                    name=name,
                    source=source,
                    type=type_obj,
                    fuel_type=fuel_type,
                    price_range=price_range,
                    vechicle_number=vechicle_number,
                    vechicle_model=vechicle_model,
                    image=image,
                    document=document,
                    color=color,
                    driver=driver_obj,
                    staff=staff_obj,
                    total_seats=total_seats,
                    price=price,
                   
                )
                
                Commission.objects.create(rate=commission_rate,bus_reserve=bus_reserve)                
                
                return redirect('vehicle_reservation')
            except Exception as e:
                print(f"Error creating reservation: {str(e)}")
                context['error'] = str(e)

        elif 'delete_reservation' in request.POST:
            reservation_id = request.POST.get('reservation_id')
            try:
                reservation = BusReservation.objects.get(id=reservation_id)
                reservation.delete()
                return redirect('vehicle_reservation')
            except BusReservation.DoesNotExist:
                context['error'] = "Reservation not found."

    return render(request, 'admin/manage_reservation.html', context)



@login_required
def edit_vehicle(request, id):
    """
    Handles GET and POST for editing a single BusReservation.
    """
    reservation = get_object_or_404(BusReservation, id=id)
    user = request.user
    transportation_company = getattr(user, 'transportation_company', None)

    # Filter available drivers and staff from same company
    staffs=None
    drivers=None
    if transportation_company:
        staffs = Staff.objects.filter(transportation_company=transportation_company)
        drivers = Driver.objects.filter(transportation_company=transportation_company)
    else:
        staffs = Staff.objects.all()
        drivers = Driver.objects.all()
        
    
    commission=Commission.objects.get(bus_reserve=reservation)
    vechicle_types = VechicleType.objects.all()
    transportation_company=TransportationCompany.objects.all()
   

    if request.method == 'POST':
        try:
            reservation.name = request.POST.get('name', reservation.name)
            type_name = request.POST.get('type')
            if type_name:
                reservation.type = VechicleType.objects.get(name=type_name)

            
            reservation.price_range=request.POST.get('price_range',reservation.price_range)
            reservation.vechicle_number = request.POST.get('vehicle_number', reservation.vechicle_number)
            reservation.vechicle_model = request.POST.get('vehicle_model', reservation.vechicle_model)
            reservation.color = request.POST.get('color', reservation.color)
            reservation.source=request.POST.get('source')

            driver_id = request.POST.get('driver_id')
            reservation.driver = Driver.objects.get(id=driver_id) if driver_id else None

            staff_id = request.POST.get('staff_id')
            reservation.staff = Staff.objects.get(id=staff_id) if staff_id else None

            reservation.total_seats = request.POST.get('total_seats', reservation.total_seats)
            reservation.price = request.POST.get('price', reservation.price)

            transportation_company_id=request.POST.get('transportation_company_id')
            if transportation_company_id:
                transportation_company=TransportationCompany.objects.get(id=transportation_company_id)
            
            commission=Commission.objects.get(bus_reserve=reservation)
            commission.rate=request.POST.get('commission_rate')
            commission.save()
            
            reservation.save()
            messages.success(request,f'Vehicle {reservation.vechicle_number} Updated Successfully  ')
            return redirect('vehicle_reservation')
        except Exception as e:
            print(f"Error updating reservation: {str(e)}")
            return render(request, 'admin/edit_reservation.html', {
                'reservation': reservation,
                'vechicle_types': vechicle_types,
                'unassigned_drivers': drivers,
                'unassigned_staff': staffs,
                'error': str(e)
            })

    return render(request, 'admin/edit_reservation.html', {
        'fuel_types':BusReservation.FUEL_TYPE,
        'reservation': reservation,
        'vechicle_types': vechicle_types,
        'unassigned_drivers': drivers,
        'unassigned_staff': staffs,
        'transportation_company':transportation_company,
        'commission_rate':commission.rate
    })
    
# ====== Delete Vehicle reservation ========

@login_required
def delete_vehicle(request, id):
    try:
        reservation = get_object_or_404(BusReservation, id=id)
        vehicle_number = reservation.vechicle_number 
        reservation.delete()
        messages.success(request, f"Vehicle  {vehicle_number}reservation deleted successfully")
        
    except Exception as e:
        messages.error(request, f"Error deleting reservation: {str(e)}")
        
    return redirect('vehicle_reservation')



# ===========
#   Vechicle Type
# ===========

@login_required
def vechicle_type_list(request):
    # Get the current user's transportation company
    transportation_company = None
    if hasattr(request.user, 'transportation_company'):
        transportation_company = request.user.transportation_company
    
    # Get all vehicle types
    vehicle_types = VechicleType.objects.all()
    
    # Process form submission for adding new vehicle type
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        if name:
            VechicleType.objects.create(name=name, image=image)
            messages.success(request, "Vehicle type added successfully!")
            return redirect('vehicle_type_list')
    
    # Add vehicle count for each type from the user's transportation company
    for vehicle_type in vehicle_types:
        if transportation_company:
            # Count vehicles of this type associated with the user's transportation company
            vehicle_count = BusReservation.objects.filter(
                type=vehicle_type,
                transportation_company=transportation_company
            ).count()
            vehicle_type.vehicle_count = vehicle_count
        else:
            vehicle_count = BusReservation.objects.filter(
                type=vehicle_type,
                
            ).count()
            vehicle_type.vehicle_count = vehicle_count
            
    
    return render(request, 'admin/vechicle_type_list.html', {'vehicle_types': vehicle_types})



@login_required
def edit_vechicle_type(request, id):
    vechicle_type = get_object_or_404(VechicleType, id=id)

    if request.method == 'POST':
        vechicle_type.name = request.POST.get('name', vechicle_type.name)
        if 'image' in request.FILES:
            vechicle_type.image = request.FILES['image']
        vechicle_type.save()
        messages.success(request, "Vehicle type updated successfully!")
        return redirect('vehicle_type_list')

    return render(request, 'admin/edit_vechicle_type.html', {'vechicle_type': vechicle_type})   


@login_required
def delete_vechicle_type(request, id):
    vechicle_type = get_object_or_404(VechicleType, id=id)
    vechicle_type.delete()
    messages.success(request, "Vehicle type deleted successfully!")
    return redirect('vehicle_type_list')


# ====== Vehicle Type all associated Vehicle list ========
@login_required
def vehicleType_vehicle_list(request, id):
    user = request.user
    transportation_company = getattr(user, 'transportation_company', None)
    vehicle_type = VechicleType.objects.get(id=id)
    
    if transportation_company:
        vehicles = BusReservation.objects.filter(
            transportation_company=transportation_company,
            type=vehicle_type
        )
    else:
        vehicles = BusReservation.objects.filter(type=vehicle_type)
    
    context = {
        'vehicle_type': vehicle_type,
        'context': vehicles
    }
    return render(request, 'admin/vehicle_type_details_list.html', context)
    


# =============
#   Route
# ============

def route_list_and_add(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        distance = request.POST.get('distance')
        estimated_time = request.POST.get('estimated_time')
        image = request.FILES.get('image')
        sub_routes = request.POST.getlist('sub_routes')  # This must be ordered from frontend

        if source and destination and distance and estimated_time:
            # Create forward route
            route = Route.objects.create(
                source=source,
                destination=destination,
                distance=distance,
                estimated_time=estimated_time,
                image=image
            )

            # Add sub-routes
            if sub_routes:
                route.sub_routes.set(sub_routes)

                if route.sub_routes.count() > Route.MAX_SUBROUTES:
                    route.delete()
                    messages.error(request, f"Maximum {Route.MAX_SUBROUTES} sub-routes allowed per route.")
                    return redirect('route_list_add')

                # Create SeachSubRoute with order
                for index, sub_id in enumerate(sub_routes):
                    SearchSubRoute.objects.create(
                        route=route,
                        subroute_id=sub_id,
                        order=index + 1
                    )

            # Create reverse route
            reverse_route = Route.objects.create(
                source=destination,
                destination=source,
                distance=distance,
                estimated_time=estimated_time,
                image=image
            )

            # Add reverse subroutes (reversed order)
            if sub_routes:
                reversed_subroutes = list(reversed(sub_routes))
                reverse_route.sub_routes.set(reversed_subroutes)

                for index, sub_id in enumerate(reversed_subroutes):
                    SearchSubRoute.objects.create(
                        route=reverse_route,
                        subroute_id=sub_id,
                        order=index + 1
                    )

            messages.success(request, "Route and reverse route added successfully.")
            return redirect('route_list_add')

    # Pagination
    routes_list = Route.objects.all().order_by('source')
    paginator = Paginator(routes_list, 10)
    page_number = request.GET.get('page')
    routes = paginator.get_page(page_number)

    sub_routes = SubRoutes.objects.all()
    return render(request, 'admin/manage_routes.html', {'routes': routes, 'sub_routes': sub_routes})



def edit_route(request, id):
    route = get_object_or_404(Route, id=id)
    print(request.POST)  # For debugging
    if request.method == 'POST':
        route.source = request.POST.get('source')
        route.destination = request.POST.get('destination')
        route.distance = request.POST.get('distance')
        route.estimated_time = request.POST.get('estimated_time')
        sub_routes_input = request.POST.get('sub_routes', '').split(',')

        # Handle image update
        if request.FILES.get('image'):
            if route.image:
                route.image.delete(save=False)
            route.image = request.FILES.get('image')

        # Process sub-routes
        sub_route_ids = []
        for sub_route in sub_routes_input:
            sub_route = sub_route.strip()
            if not sub_route:
                continue
            if sub_route.startswith('new:'):
                # Create new sub-route
                name = sub_route[4:].strip()
                if name and not SubRoutes.objects.filter(name__iexact=name).exists():
                    new_sub_route = SubRoutes.objects.create(name=name)
                    sub_route_ids.append(new_sub_route.id)
            elif sub_route.startswith('update:'):
                # Update existing sub-route
                try:
                    parts = sub_route.split(':', 2)
                    if len(parts) == 3:
                        sub_route_id = int(parts[1])
                        new_name = parts[2].strip()
                        if new_name and not SubRoutes.objects.filter(name__iexact=new_name).exclude(id=sub_route_id).exists():
                            sub_route_obj = SubRoutes.objects.get(id=sub_route_id)
                            sub_route_obj.name = new_name
                            sub_route_obj.save()
                            sub_route_ids.append(sub_route_id)
                except (ValueError, SubRoutes.DoesNotExist):
                    continue
            else:
                # Existing sub-route (unchanged)
                try:
                    sub_route_id = int(sub_route)
                    if SubRoutes.objects.filter(id=sub_route_id).exists():
                        sub_route_ids.append(sub_route_id)
                except ValueError:
                    continue

        # Update sub-routes
        route.sub_routes.set(sub_route_ids)
        if route.sub_routes.count() > Route.MAX_SUBROUTES:
            messages.error(request, f"Maximum {Route.MAX_SUBROUTES} sub-routes allowed per route.")
            return redirect('edit_route', id=id)

        route.save()
        messages.success(request, "Route updated successfully.")
        return redirect('route_list_add')

    sub_routes = route.sub_routes.all()  # Only pass the route's sub-routes
    return render(request, 'admin/edit_route.html', {'route': route, 'sub_routes': sub_routes})


def delete_route(request, id):
    route = get_object_or_404(Route, id=id)
    if request.method == 'POST':
        route.delete()
        messages.success(request, "Route deleted successfully.")
        return redirect('route_list_add')
    return redirect('route_list_add')



# ======= ==============
# Bus List of one Route
# =====================
def route_bus_list(request, id):
    route = get_object_or_404(Route, id=id)
    buses = Bus.objects.filter(schedule__route_id=id).distinct()
    
    total_buses = buses.count()

    context = {
        'route': route,
        'buses': buses,
        'total_buses': total_buses,
    }
    return render(request, 'admin/route_buslist.html', context)


# ====== Json data for bus data of Route  =======
class BusDetails(APIView):
    def get(self, request, *args, **kwargs):
        bus_id = kwargs.get('id')
        try:
            bus = Bus.objects.get(id=bus_id)
            serializer = BusSerializer(bus)
            return Response({"success":True,'data':serializer.data}, status=200)
        except Bus.DoesNotExist:
            return Response({"error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)
            


# ========= Schedule list ===========


def schedule_list(request):
    
    try:
        
        Schedule.update_all_status()
        user = request.user
        transportation_company = getattr(user, "transportation_company", None)
        
        if request.method == "POST":
            try:
                # Get form data
                route_id = request.POST.get("route")
                bus_id = request.POST.get("bus")
                departure_input = request.POST.get("departure_time")
                arrival_input = request.POST.get("arrival_time")
                price = request.POST.get("price")
                original_price=request.POST.get('original_price')

                # Validate route and bus
                route = Route.objects.get(id=route_id)
                bus = Bus.objects.get(id=bus_id)

                # Parse datetime fields
                departure_time = datetime.strptime(departure_input, "%Y-%m-%dT%H:%M")
                arrival_time = datetime.strptime(arrival_input, "%Y-%m-%dT%H:%M")

                if arrival_time <= departure_time:
                    raise ValueError("Arrival time must be after departure time")

                # Make timezone-aware
                tz = timezone.get_current_timezone()
                departure_time = timezone.make_aware(departure_time, tz)
                arrival_time = timezone.make_aware(arrival_time, tz)

                # Check for overlapping schedules for the same bus
                overlap_exists = Schedule.objects.filter(
                    bus=bus,
                    departure_time__lte=arrival_time,
                    arrival_time__gte=departure_time,
                ).exists()

                if overlap_exists:
                    messages.error(request, "A schedule already exists for this bus with overlapping times.")
                    return redirect("schedule_list")

                # Create schedule and store the reference
                schedule = Schedule.objects.create(
                    route=route,
                    bus=bus,
                    available_seats=bus.total_seats,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    price=price,
                    original_price=original_price,
                    transportation_company=transportation_company
                )

                # Bus layout booking
                bus_layout = BusLayout.objects.get(bus=bus)
                SeatLayoutBooking.objects.create(
                    schedule=schedule,
                    layout_data=bus_layout.layout_data
                )
                
                messages.success(request, "Schedule created successfully!")
                return redirect("schedule_list")

            except Exception as e:
                messages.error(request, f"Error creating schedule: {str(e)}")
                return redirect("schedule_list")

        # Handle GET (list, search, filter)
        selected_date_str = request.GET.get('date')
        search_query = request.GET.get('search', '').strip()
        route_id = request.GET.get('route')
        time_range = request.GET.get('time_range', '').strip()

        schedules = Schedule.objects.all().order_by('-date')
        if transportation_company:
            schedules = schedules.filter(transportation_company=transportation_company)

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
        filters = Q()
        if search_query:
            filters &= (
                Q(route__source__icontains=search_query) |
                Q(route__destination__icontains=search_query) |
                Q(bus__bus_number__icontains=search_query) |
                Q(price__icontains=search_query)
            )
        if time_range:
            filters &= Q(status=time_range)
        if route_id:
            filters &= Q(route_id=route_id)

        if filters:
            schedules = schedules.filter(filters).distinct()

        all_routes = Route.objects.all()
        all_buses = Bus.objects.filter(transportation_company=transportation_company) if transportation_company else Bus.objects.all()

        context = {
            'schedules': schedules,
            'all_routes': all_routes,
            'all_buses': all_buses,
            'selected_date': selected_date.isoformat() if selected_date else '',
            'search_query': search_query,
            'route_id': int(route_id) if route_id else None,
            'time_range': time_range,
        }
    except Exception as e:
        print(e)

    return render(request, "admin/manage_schedule.html", context)
    

def schedule_edit(request, id):
    user = request.user
    all_buses = Bus.objects.none()
    transportation_company = getattr(user, 'transportation_company', None)
    if transportation_company:
        all_buses = Bus.objects.filter(transportation_company=transportation_company)
    else:
        all_buses = Bus.objects.all()
        
    schedule = get_object_or_404(Schedule, id=id)
    
    if request.method == "POST":
        # Get the data from the POST request
        route = Route.objects.get(id=request.POST.get("route"))
        bus = Bus.objects.get(id=request.POST.get("bus"))
        
        # Convert the datetime strings into actual datetime objects
        departure_time_str = request.POST.get("departure_time")
        arrival_time_str = request.POST.get("arrival_time")
        
        # Convert string to datetime object
        departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M')
        arrival_time = datetime.strptime(arrival_time_str, '%Y-%m-%dT%H:%M')
        
        # Update the schedule
        schedule.route = route
        schedule.bus = bus
        schedule.departure_time = departure_time
        schedule.arrival_time = arrival_time
        schedule.original_price=request.POST.get('original_price')
        schedule.price = request.POST.get("price")
        schedule.save()
        
        messages.success(request,"Schedule Updated Successfully")
        return redirect("schedule_list")
    
    all_routes = Route.objects.all()
    
    return render(request, "admin/edit_schedule.html", {
        "schedule": schedule,
        "all_routes": all_routes,
        "all_buses": all_buses
    })


def schedule_delete(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    schedule.delete()
    messages.success(request,"Schedule Deleted Successfully")
    return redirect("schedule_list")


# ======= Bus  details schedule =========
def schedule_bus_details(request, id):
        print(id)
        schedule = Schedule.objects.get(id=id)
        bus = schedule.bus
        layout = get_object_or_404(SeatLayoutBooking, schedule=schedule)

        total_booked = bus.total_seats - schedule.available_seats

        seat_layout_with_bookings = []
        booked_seats = {}
        booked_seat = 0

        for booking in Booking.objects.filter(schedule=schedule):
            for seat in booking.seat:
                booked_seats[seat] = {
                    "user": booking.user.full_name,
                    "booking_id": booking.id
                }
                booked_seat += 1

        total_amount = booked_seat * schedule.price

        for row in layout.layout_data:
            enhanced_row = []
            for seat in row:
                if seat == 0:
                    enhanced_row.append(0)
                else:
                    seat_name = seat["seat"]
                    seat_status = seat["status"]
                    seat_info = {
                        "seat": seat_name,
                        "status": seat_status,
                        "user": booked_seats.get(seat_name, {}).get("user", None) if seat_status == "booked" else None,
                        "booking_id": booked_seats.get(seat_name, {}).get("booking_id", None) if seat_status == "booked" else None
                    }
                    enhanced_row.append(seat_info)
            seat_layout_with_bookings.append(enhanced_row)

        return render(request, 'admin/schedule_buslist.html', {
            'bus': bus,
            'layout': layout,
            'schedule': schedule,
            'seat_layout': seat_layout_with_bookings,
            'total_amount': total_amount,
            'booked_seat': booked_seat,
            'total_booked': total_booked,
        })
        
        
# ======= Bookinglist of one User ==============
def booking_details(request, id):
    booking = get_object_or_404(Booking, id=id)
    count = len(booking.seat)
    total_price = count * booking.schedule.price
    
    data = {
        'id':booking.id,
        'user': booking.user.full_name,
        'user_phone': booking.user.phone,
        'bus_number': booking.bus.bus_number,
        'source': booking.schedule.route.source,
        'destination': booking.schedule.route.destination,
        'booking_status': booking.booking_status,
        'seat': booking.seat,
        'booked_at': booking.booked_at,
        'total_price': total_price,
        'total_seat': count,
    }
    
    return JsonResponse(data)


    # ========= Change Bus availability ==========
def change_bus_availability(request):
        try:
            # Parse JSON data from request body
            data = json.loads(request.body.decode('utf-8'))
            schedule_id = data.get('schedule_id')
            seat = data.get('seat_number') 
            seat_numbers=[]
            seat_numbers.append(seat)
            print(seat_numbers)

            status = data.get('status')

            print(data)  
            schedule = Schedule.objects.get(id=schedule_id)
            
            seat_booking = SeatLayoutBooking.objects.get(schedule=schedule)
            
            if status == 'available':
                print("=======")
                
                seat_booking.mark_seat_available(seat_numbers)
                schedule.available_seats+=1
                
            elif status == 'unavailable':
                print("--------")
                seat_booking.mark_seat_unavailable(seat_numbers)
                schedule.available_seats-=1
                
            schedule.save()
            
            return JsonResponse({'success': True, 'status': status})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
        except Schedule.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Schedule not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        
        
# ========== Booking Management  =================
def booking_management(request):
    user=request.user
    transportation_company=getattr(user, 'transportation_company', None)    
    try:
        if transportation_company:
            bus_reserve_data = BusReservationBooking.objects.filter(bus_reserve__transportation_company=transportation_company).order_by('-created_at')
            booking_data = Booking.objects.filter(bus__transportation_company=transportation_company).order_by('-booked_at')
        else:
            bus_reserve_data = BusReservationBooking.objects.all().order_by('-created_at')
            booking_data = Booking.objects.all().order_by('-booked_at')
            
        bus_reserve_paginator = Paginator(bus_reserve_data, 8)  # 8 items per page
        page_number_bus_reserve = request.GET.get('page')
        bus_reserve_page = bus_reserve_paginator.get_page(page_number_bus_reserve)
    
        booking_paginator = Paginator(booking_data, 10) 
        page_number_booking = request.GET.get('page')
        booking_page = booking_paginator.get_page(page_number_booking)

        return render(request, 'admin/manage_booking.html', {
            'bus_reserve_data': bus_reserve_page,
            'booking_data': booking_page,
        })
    except Exception as e:
        return render(request, 'admin/manage_booking.html', {'error': str(e)})



# Booking sttatsus update
def booking_status_update(request,booking_id):
    print(request.POST)
    if request.method == 'POST':
        status=request.POST.get('status')
        
        booking_obj=Booking.objects.get(id=booking_id)
        booking_obj.booking_status=status
        booking_obj.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def reservationBooking_update(request, id):
    user=request.user
    reservation=BusReservationBooking.objects.get(id=id)
    transportation_company=getattr(user,'transportation_company',None)
    if request.method == "POST":
        print(request.POST)
        try:
            print("POST Data:", request.POST)

            source=request.POST.get('source')
            destination=request.POST.get('destination')
            agreed_price=request.POST.get('agreed_price')
            start_date=request.POST.get('start_date')
            end_date=request.POST.get('end_date')
            date=request.POST.get('date')
            status=request.POST.get('status')
            vechicle_number=request.POST.get('vechicle_number')
            driver_id=request.POST.get('driver_id')
            staff_id=request.POST.get('staff_id')
            
            driver_obj=Driver.objects.get(id=driver_id)
            staff_obj=Staff.objects.get(id=staff_id)
            
            reservation.bus_reserve.vechicle_number=vechicle_number
            reservation.bus_reserve.driver=driver_obj
            reservation.bus_reserve.staff=staff_obj
            reservation.source=source 
            reservation.destination=destination
            reservation.agreed_price=agreed_price
            reservation.start_date=start_date
            reservation.end_date=end_date
            reservation.date=date
            reservation.status=status
            reservation.save()
            messages.success(request,'Vehicle Reservation updated Successfully ')
            return redirect('booking_list')
    
        except Exception as e:
            print("Error:", str(e))
            messages.error(request, "Something went wrong.")
            return redirect('booking_list')
    driver= Driver.objects.filter(transportation_company=transportation_company) if transportation_company  else Driver.objects.all()
    staff = Staff.objects.filter(transportation_company=transportation_company) if transportation_company else Staff.objects.all()
    bus=Bus.objects.filter(transportation_company=transportation_company) if transportation_company else Bus.objects.all()

    data={
        'driver':driver,
        'staff':staff,
        'reservation':reservation,
        'bus':bus
        
        
        }

    return render(request,'admin/edit_booking_reservation.html',data)


def delete_vehicle_reservation_booking(request,id):
    vehicle_reservation=BusReservationBooking.objects.get(id=id)
    vehicle_reservation.delete()
    messages.success(request,'Successfully deleted vehicle reservation')
    return redirect('booking_list')
    
    
# ========== Reports details  ===========

def report_analysis_view(request):
    current_month, current_year = now().month, now().year
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1

    # Current Month Data
    monthly_revenue = Payment.objects.filter(
        created_at__month=current_month, 
        created_at__year=current_year, 
        payment_status="completed"
    ).aggregate(total=Sum('booking__schedule__price'))['total'] or 0
    monthly_commission = Payment.objects.filter(created_at__month=current_month, created_at__year=current_year).aggregate(total=Sum('commission_deducted'))['total'] or 0
    total_bookings = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year).count()
    canceled_bookings = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year, booking_status='canceled').count()
    top_buses = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year).values(bus_number=F('bus__bus_number')).annotate(total_bookings=Count('id')).order_by('-total_bookings')[:5]
    top_customers = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year).values(customer=F('user__full_name')).annotate(total_bookings=Count('id')).order_by('-total_bookings')[:5]

    # Previous Month Data (for comparison)
    prev_revenue = Payment.objects.filter(created_at__month=prev_month, created_at__year=prev_year).aggregate(total=Sum('booking__schedule__price'))['total'] or 0
    prev_bookings = Booking.objects.filter(booked_at__month=prev_month, booked_at__year=prev_year).count()

    # Format numbers with commas using Python's locale-independent method
    def format_number(value):
        return "{:,}".format(int(value)) if value else "0"

    # Calculate differences and cancellation rate in the view
    revenue_diff = monthly_revenue - prev_revenue
    bookings_diff = total_bookings - prev_bookings
    cancellation_rate = (canceled_bookings / total_bookings * 100) if total_bookings > 0 else 0

    return render(request, 'admin/report_analysis.html', {
        "month_year": f"{current_month}-{current_year}",
        "monthly_revenue": format_number(monthly_revenue),
        "monthly_commission": format_number(monthly_commission),
        "total_bookings": format_number(total_bookings),
        "canceled_bookings": format_number(canceled_bookings),
        "top_buses": top_buses,
        "top_customers": top_customers,
        "prev_revenue": format_number(prev_revenue),
        "prev_bookings": format_number(prev_bookings),
        "revenue_diff": format_number(abs(revenue_diff)),
        "bookings_diff": format_number(abs(bookings_diff)),
        "revenue_diff_positive": revenue_diff > 0,
        "bookings_diff_positive": bookings_diff > 0,
        "cancellation_rate": cancellation_rate,
    })
    

# ========================
# Settings 
#=========================
def system_settings_view(request):
    system = System.objects.first()

    if request.method == "POST":
    
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        image = request.FILES.get('image')

        if system:
            system.name = name
            system.email = email
            system.phone = phone
            system.address = address
            
            system.image = image
            system.save()
            messages.success(request, "System settings updated successfully!")
        else:
            messages.error(request, "Error: No system settings found.")

        return redirect("system_settings")

    return render(request, "admin/manage_settings.html", {"system": system})


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.defaulttags import register
# Register a custom filter for template to calculate commission
@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    return float(value) / float(arg)


#========= Payment and Commission =============
@login_required 
def bus_payment_details(request):
        user = request.user
        user_company = getattr(user, 'transportation_company', None)
        
        buses = Bus.objects.all()
        if user_company:
            buses = buses.filter(transportation_company=user_company)

        # Get all payments for buses
        payments_query = Payment.objects.filter(
            booking__bus__in=buses,
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

        # Calculate earnings and commission per bus
        bus_earnings = []
        for bus in buses:
            # Get commission rate for this bus
            commission = Commission.objects.filter(bus=bus).first()
            commission_rate = commission.rate if commission else Decimal('0.00')

            # Get all completed payments for this bus
            bus_payments = payments_query.filter(booking__bus=bus)
            
            # Calculate total earnings (total payment amount)
            total_earning = bus_payments.aggregate(
                total=Sum('booking__schedule__price')
            )['total'] or Decimal('0.00')
            
            # Calculate commission
            total_commission = (total_earning * commission_rate / 100) if commission_rate else Decimal('0.00')
            
            # Calculate net earnings
            net_earning = total_earning - total_commission
            
            # Count completed trips
            total_trips = Schedule.objects.filter(
                bus=bus, 
                status="finished"
            ).count()
            print("Total Trips" ,total_trips)
            bus_earnings.append({
                'bus': bus,
                'rate': float(commission_rate),
                'bus_number': bus.bus_number,
                'bus_type': bus.bus_type,
                'total_earning': float(total_earning),
                'total_commission': float(total_commission),
                'net_earning': float(net_earning),
                'total_trips': total_trips
            })

        bus_earnings.sort(key=lambda x: x['total_earning'], reverse=True)
        
        # Paginate bus earnings
        earnings_per_page = 5
        earnings_paginator = Paginator(bus_earnings or [], earnings_per_page)
        earnings_page = request.GET.get('earnings_page')
        
        try:
            paginated_earnings = earnings_paginator.page(earnings_page)
        except PageNotAnInteger:
            paginated_earnings = earnings_paginator.page(1)
        except EmptyPage:
            paginated_earnings = earnings_paginator.page(earnings_paginator.num_pages)

        # Calculate overall totals
        total_amount = sum(e['total_earning'] for e in bus_earnings)
        total_commission = sum(e['total_commission'] for e in bus_earnings)
        total_received = sum(e['net_earning'] for e in bus_earnings)
        total_trips = sum(e['total_trips'] for e in bus_earnings)

        # Get today's completed payments
        today = timezone.now().date()
        today_payments = Payment.objects.filter(
            payment_status="completed",
            created_at__date=today,
            booking__bus__in=buses
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
            'bus_earnings': paginated_earnings,
            'total_amount': float(total_amount),
            'total_commission': float(total_commission),
            'total_received': float(total_received), 
          
            'date_filter': date_filter,
        }

        return render(request, 'admin/bus_payment_details.html', context)





# ==== Bus Seat Earning details ========
from django.utils.timezone import make_aware
@login_required
def bus_earning_details_schedule(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
        schedules = Schedule.objects.filter(
            bus=bus,
            departure_time__gte=start_date,
            departure_time__lte=end_date
        ).order_by('-departure_time')
    else:
        schedules = Schedule.objects.filter(bus=bus).order_by('-departure_time')

    schedule_data = []

    for schedule in schedules:
        payments = Payment.objects.filter(
            booking__schedule=schedule,
            payment_status='completed'
        )

        try:
            commission_obj = Commission.objects.get(bus=bus)
            commission_rate = commission_obj.rate
        except Commission.DoesNotExist:
            commission_rate = 0

        total_paid = 0
        total_commission = 0
        total_net = 0

        for payment in payments:
            price = schedule.price
            commission = (price * commission_rate) / 100
            net = price - commission

            total_paid += price
            total_commission += commission
            total_net += net

        schedule_data.append({
            'schedule': schedule,
            'commission_rate': commission_rate,
            'total_paid': total_paid,
            'total_commission': total_commission,
            'total_net': total_net,
            'transactions': payments.count()
        })

    # Add pagination
    paginator = Paginator(schedule_data, 10)  # Show 10 schedules per page
    page = request.GET.get('page')
    try:
        schedules_page = paginator.page(page)
    except PageNotAnInteger:
        schedules_page = paginator.page(1)
    except EmptyPage:
        schedules_page = paginator.page(paginator.num_pages)

    context = {
        'bus': bus,
        'start_date': start_date.date() if start_date else None,
        'end_date': end_date.date() if end_date else None,
        'schedule_earnings': schedules_page,
        'is_paginated': True if schedules.count() > 10 else False
    }

    return render(request, 'admin/bus_earning_details.html', context)


@login_required
def bus_earning_payment(request, schedule_id):
        try:
            schedule = get_object_or_404(Schedule, id=schedule_id)

            # Get start and end date from request, default to None if not provided
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            payments = Payment.objects.filter(booking__schedule=schedule,payment_status="completed").order_by('-created_at')

            # If start_date and end_date are provided, convert them to timezone-aware datetimes and filter payments 
            if start_date and end_date:
                start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
                payments = payments.filter(created_at__gte=start_date, created_at__lte=end_date)

            # Initialize totals
            total_paid = 0
            total_commission = 0 
            total_net = 0

            earnings_list = []
            for payment in payments:

                commission_obj = Commission.objects.filter(bus=schedule.bus).first()
                
                # Calculate amounts
                commission_rate = commission_obj.rate if commission_obj else 0
                price = payment.booking.schedule.price or 0
                commission = (price * commission_rate) / 100 if commission_rate > 0 else 0
                net_earning = price - commission

                # Update totals
                total_paid += price
                total_commission += commission
                total_net += net_earning

                passenger_name = payment.user.full_name if payment.user else 'Unknown'
                transaction_id = payment.transaction_id or 'N/A'

                earnings_list.append({
                    'seat_number': payment.booking.seat,
                    'passenger': passenger_name,
                    'amount_paid': price,
                    'commission': commission,
                    'commission_rate': commission_rate,
                    'net_earning': net_earning,
                    'payment_date': payment.created_at,
                    'transaction_id': transaction_id,
                    'booking_id': payment.booking.id
                })

            # Get commission rate
            commission_rate = Commission.objects.get(bus=schedule.bus).rate

            # Calculate total earnings summary
            total_earnings = {
                'total_paid': total_paid,
                'total_commission': total_commission,
                'total_net': total_net
            }

            context = {
                'commission_rate': commission_rate,
                'bus': schedule.bus,
                'earnings_list': earnings_list,
                'start_date': start_date.date() if start_date else None,
                'end_date': end_date.date() - timedelta(days=1) if end_date else None,
                'total_earnings': total_earnings
            }

            return render(request, 'admin/bus_earning_payments.html', context)
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('bus_list')


# ======= vehicle reservation =========
@login_required
def reservation_payment_details(request):
    user = request.user
    user_company = getattr(user, 'transportation_company', None)

    reservations = BusReservationBooking.objects.all()
    if user_company:
        reservations = reservations.filter(bus_reserve__transportation_company=user_company)
    
    total_earning = 0
    total_commission = 0
    commission = Commission.objects.filter(bus_reserve__in=[r.bus_reserve for r in reservations])

    
    for item in commission:
        item.total_trips=item.bus_reserve.reservation_booking.all().count()
        item.net_earning = item.total_earnings - item.total_commission
        total_earning += item.total_earnings
        total_commission += item.total_commission

    net_received = total_earning - total_commission

    paginator = Paginator(commission, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    vehicle_types = VechicleType.objects.all()

    context = {
        'reservation_bookings': page_obj,
        'total_earning': total_earning,
        'total_commission': total_commission,
        'net_received': net_received,
        'page_obj': page_obj,
        'vehicle_types': vehicle_types,
    }

    return render(request, 'admin/reservation_payment_details.html', context)


from django.utils.dateparse import parse_date
@login_required
def vehicle_reservation_earings_details(request, vehicle_id):
   
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    reservations = BusReservationBooking.objects.filter(bus_reserve__id=vehicle_id)
    if start_date and end_date:
        try:
            start_date_parsed = parse_date(start_date)
            end_date_parsed = parse_date(end_date)
            if start_date_parsed and end_date_parsed:
                reservations = reservations.filter(
                    start_date__gte=start_date_parsed,
                    start_date__lte=end_date_parsed
                )
        except ValueError:
            pass
    vehicle_obj=BusReservation.objects.get(id=vehicle_id)
    return render(request, 'admin/vehicle_reservation_earnings.html', {
        'reservation': reservations,
        'vehicle_number':vehicle_obj.vechicle_number,
        'vehicle_type':vehicle_obj.type.name,
        
        
        
    })


# ========= Vehicle Details of payments =============
@login_required
def vehicle_details_payment(request,id):
    vehicle_booking = BusReservationBooking.objects.get(id=id)
    context = {
        'vehicle_booking': vehicle_booking
    }
    return render(request, 'admin/vehicle_details.html', context)
    
    





# =================
# Trips
# =================
@login_required 
def all_trips(request):
    user = request.user
    transportation_company = getattr(user, 'transportation_company', None)
    
    # Get all trips for client-side filtering
    trips = Trip.objects.all().order_by('-scheduled_departure')
    
    # Filter by company if user belongs to one
    if transportation_company:
        trips = trips.filter(bus__transportation_company=transportation_company)
        
    # Get distinct routes for filter dropdown
    routes = Route.objects.filter(trip__in=trips).distinct() if transportation_company else Route.objects.all()
    
    context = {
        'trips': trips,
        'status_choices': Trip._meta.get_field('status').choices,
        'routes': routes,
    }
    
    return render(request, 'admin/all_trips.html', context)




# ========= Notification ============
@login_required
def all_notification(request):
    notification_system = Notification.objects.filter(type='system').order_by('-created_at')
    notification_user = Notification.objects.filter(type='booking').order_by('-created_at')

    system_page = request.GET.get('system_page', 1)
    user_page = request.GET.get('user_page', 1)

    system_paginator = Paginator(notification_system, 10)
    user_paginator = Paginator(notification_user, 10)

    system_notifications = system_paginator.get_page(system_page)
    user_notifications = user_paginator.get_page(user_page)

    return render(request, 'admin/all_notifications.html', {
        'system_notifications': system_notifications,
        'user_notifications': user_notifications  # don't use 'user' here
    })

        
        

@login_required
def add_notification(request):
    if request.method == 'POST':
        print(request.POST)
        
        title = request.POST.get('title')
        message = request.POST.get('message')

        Notification.send_notification_to_all_users(title, message)
        messages.success(request, "Notification added successfully!")
        return redirect('all_notification')
    return render(request, 'admin/add_notification.html')     


@login_required
def edit_notification(request, id):
    notification = get_object_or_404(Notification, id=id)
    
    if request.method == 'POST':
        notification.title = request.POST.get('title')
        notification.message = request.POST.get('message')
        notification.save()
        messages.success(request, "Notification updated successfully!")
        return redirect('all_notification')

    return render(request, 'admin/edit_notification.html', {'notification': notification})

@login_required
def delete_notification(request, id):
    notification = get_object_or_404(Notification, id=id)
    notification.delete()
    messages.success(request, "Notification deleted successfully!")
    return redirect('all_notification')



# views.py


@login_required
def payment_list(request):
    """
    Display paginated list of all payments with filtering options
    """
    user = request.user
    transportation_company = getattr(user, 'transportation_company', None)
    
    # Base queryset with proper joins
    payments = Payment.objects.select_related(
        'user', 
        'booking', 
        'booking__bus',
        'booking__bus__transportation_company'
    ).order_by('-created_at')
    
    # Filter by transportation company for sub-admin
    if transportation_company:
        payments = payments.filter(booking__bus__transportation_company=transportation_company)

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




def privacy(request):
    return render(request,'privacy.html')
    