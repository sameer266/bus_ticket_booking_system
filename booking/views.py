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

import json


from custom_user.models import CustomUser,System,TransportationCompany
from route.models import Route, Schedule, Trip,Notification
from bus.models import Bus,Driver,Staff,BusReservation,BusLayout,VechicleType,SeatLayoutBooking
from booking.models import Commission, Booking,Payment,BusReservationBooking


from route.serializers import (
    BusSerializer,
   
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


   

@login_required
def admin_dashboard(request):
    """
    Render the admin dashboard with overview statistics and recent data.
    Shows only company-specific stats if user is sub-admin.
    """
    user = request.user
    user_company = getattr(user, 'transportation_company', None)
    user_role = getattr(user, 'role', 'admin')  # default to admin if role not set

    data = {}

    if  user_company:
        # Sub-admin: only show their own company's data
        buses = Bus.objects.filter(transportation_company=user_company, is_active=True)
        commissions = Commission.objects.filter(bus__in=buses)

        user_count = CustomUser.objects.filter(
            role="customer",
            booking__bus__in=buses
        ).distinct().count()

        bus_count = buses.count()
        total_amount = commissions.aggregate(total=Sum('total_commission'))['total'] or 0
        pending_bookings = Booking.objects.filter(booking_status="pending", bus__in=buses).count()
        completed_trips = Trip.objects.filter(status="completed", bus__in=buses).count()
        booked_tickets = Booking.objects.filter(booking_status='booked', bus__in=buses).count()

        recent_booking = Booking.objects.filter(bus__in=buses).order_by('-booked_at')[:8]
        trip_data = Trip.objects.filter(bus__in=buses)[:8]

    else:
        # Admin: show all data
        user_count = CustomUser.objects.filter(role="customer").count()
        bus_count = Bus.objects.filter(is_active=True).count()
        commissions = Commission.objects.all()

        total_amount = commissions.aggregate(total=Sum('total_commission'))['total'] or 0
        pending_bookings = Booking.objects.filter(booking_status="pending").count()
        completed_trips = Trip.objects.filter(status="completed").count()
        booked_tickets = Booking.objects.filter(booking_status='booked').count()

        recent_booking = Booking.objects.all().order_by('-booked_at')[:8]
        trip_data = Trip.objects.all()[:8]

    data["total_revenue"] = total_amount
    data['total_booking_pending'] = pending_bookings
    data['total_trip_completed'] = completed_trips
    data['ticket_booked'] = booked_tickets
    data["total_active_bus"] = bus_count
    data["total_user"] = user_count

    context = {
        'data': data,
        'recent_booking': recent_booking,
        'trip_data': trip_data,
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
        return redirect("ticket_counter_list")
    except Exception as e:
        print(str(e))
        
        

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




# ========= Bus Management ========


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

    # === Staff filtering ===
    assigned_staff_ids = Bus.objects.exclude(staff=None).values_list("staff__id", flat=True)
    scheduled_staff_ids = Schedule.objects.filter(
        departure_time__gte=timezone.now(),
        bus__staff__isnull=False
    ).values_list("bus__staff__id", flat=True)

    unassigned_staff = staff.exclude(id__in=set(assigned_staff_ids) | set(scheduled_staff_ids))
    transportation_company_list=TransportationCompany.objects.all()
    # === Final context ===
    context = {
        'buses': buses,
        'transportation_company':transportation_company_list,
        'all_drivers': unassigned_drivers,
        'all_staff': unassigned_staff,
        'bus_types': Bus.VEHICLE_CHOICES,
        'feature_choices': Bus.FEATURE_CHOICES,
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

            features = request.POST.getlist('features')  # Use getlist for multiple checkbox values
            bus_image = request.FILES.get('bus_image')
            layout = request.POST.get('layout')

            driver = Driver.objects.get(id=driver_id) if driver_id else None
            staff = Staff.objects.get(id=staff_id) if staff_id else None
           
            
            commission_rate=request.POST.get('commission_rate')
            

            # Create bus
            bus = Bus.objects.create(
                bus_number=bus_number,
                bus_type=bus_type,
                driver=driver,
                staff=staff,
            
            
                total_seats=total_seats,
            
                is_active=is_active,
           
                features=features,
                bus_image=bus_image,
                transportation_company=transportation_company
            )

            # Handle layout if provided
            if layout:
                layout_data = json.loads(layout)
                BusLayout.objects.create(
                    bus=bus,
                    rows=layout_data['rows'],
                    column=layout_data['columns'],
                    layout_data=layout_data['layout'],
                    aisle_column=layout_data.get('aisleAfterColumn')
                )
            if commission_rate:
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

    context = {

        'all_drivers': drivers,
        'all_staff': staff,
        'bus_types': Bus.VEHICLE_CHOICES,
        'feature_choices': Bus.FEATURE_CHOICES,
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
            # Update basic fields
            bus.bus_number = request.POST.get('bus_number', bus.bus_number)
            bus.bus_type = request.POST.get('bus_type', bus.bus_type)
            
            # Handle driver
            driver_id = request.POST.get('driver', '')
            bus.driver = Driver.objects.get(id=driver_id) if driver_id else None
            
            # Handle staff
            staff_id = request.POST.get('staff', '')
            bus.staff = Staff.objects.get(id=staff_id) if staff_id else None
            
            
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
                bus.features = features
                
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
                'redirect': '/buses-management/'
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
        commission=Commission.objects.get(bus=bus)
        rate=commission.rate
        layout = BusLayout.objects.get(bus=bus)
        layout_data = {
            'rows': layout.rows,
            'columns': layout.column,
            'aisleAfterColumn': layout.aisle_column,
            
            'layout': layout.layout_data,
            
        }
    except BusLayout.DoesNotExist:
        layout_data = {}

    data = {
        'bus_id': bus.id,
        'bus_number': bus.bus_number,
        'bus_type': bus.bus_type,
        'rate':rate,
        'bus_image':bus.bus_image.url if bus.bus_image else '',
        'total_seats': bus.total_seats,
        'driver': bus.driver.id if bus.driver else None,
        'staff': bus.staff.id if bus.staff else None,
        'is_active': bus.is_active,
        'features': bus.features,
        'layout': json.dumps(layout_data)
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
# Vehicle Reservation (Django Template View)
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

    assigned_driver_ids = BusReservation.objects.filter(driver__isnull=False).values_list('driver__id', flat=True)
    unassigned_drivers = Driver.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_driver_ids)

    assigned_staff_ids = BusReservation.objects.filter(staff__isnull=False).values_list('staff__id', flat=True)
    unassigned_staff = Staff.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_staff_ids)

    vechicle_types = VechicleType.objects.all()

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
        'unassigned_drivers': unassigned_drivers,
        'unassigned_staff': unassigned_staff,
        'vechicle_types': vechicle_types,
        'source':source,
        'reservation_json': reservation_json,
    }

    if request.method == 'POST':
        if 'add_reservation' in request.POST:
            try:
                name = request.POST.get('name')
                type_id = request.POST.get('type')
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

                type_obj = VechicleType.objects.get(id=type_id) if type_id else None
                driver_obj = Driver.objects.get(id=driver_id) if driver_id else None
                staff_obj = Staff.objects.get(id=staff_id) if staff_id else None

                BusReservation.objects.create(
                    name=name,
                    source=source,
                    type=type_obj,
                    vechicle_number=vechicle_number,
                    vechicle_model=vechicle_model,
                    image=image,
                    document=document,
                    color=color,
                    driver=driver_obj,
                    staff=staff_obj,
                    total_seats=total_seats,
                    price=price,
                    transportation_company=transportation_company
                )
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
    assigned_driver_ids = BusReservation.objects.exclude(id=id).filter(driver__isnull=False).values_list('driver__id', flat=True)
    unassigned_drivers = Driver.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_driver_ids)

    assigned_staff_ids = BusReservation.objects.exclude(id=id).filter(staff__isnull=False).values_list('staff__id', flat=True)
    unassigned_staff = Staff.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_staff_ids)

    vechicle_types = VechicleType.objects.all()
   

    if request.method == 'POST':
        try:
            reservation.name = request.POST.get('name', reservation.name)
            type_name = request.POST.get('type')
            if type_name:
                reservation.type = VechicleType.objects.get(name=type_name)

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

            reservation.save()
            return redirect('vehicle_reservation')
        except Exception as e:
            print(f"Error updating reservation: {str(e)}")
            return render(request, 'admin/edit_reservation.html', {
                'reservation': reservation,
                'vechicle_types': vechicle_types,
                'unassigned_drivers': unassigned_drivers,
                'unassigned_staff': unassigned_staff,
                'error': str(e)
            })

    return render(request, 'admin/edit_reservation.html', {
        'reservation': reservation,
        'vechicle_types': vechicle_types,
        'unassigned_drivers': unassigned_drivers,
        'unassigned_staff': unassigned_staff,
    })
    
# ====== Delete Vehicle reservation ========

@login_required
def delete_vehicle(request, id):
    try:
        reservation = get_object_or_404(BusReservation, id=id)
        
        
            
        reservation.delete()
        messages.success(request, "Vehicle reservation deleted successfully")
        
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
        image=request.FILES.get('image')
        destination = request.POST.get('destination')
        distance = request.POST.get('distance')
        estimated_time = request.POST.get('estimated_time')

        if source and destination and distance and estimated_time:
            Route.objects.create(
                source=source,
                destination=destination,
                distance=distance,
                estimated_time=estimated_time,
                image=image
                
            )
            
            Route.objects.create(
                source=destination, destination=source,distance=distance,
                estimated_time=estimated_time,image=image
            )
            return redirect('route_list_add') 
    routes = Route.objects.all()
    return render(request, 'admin/manage_routes.html', {'routes': routes})



def edit_route(request, id):
    route = get_object_or_404(Route, id=id)

    if request.method == 'POST':
        print(request.POST)
        route.source = request.POST.get('source')
        route.destination = request.POST.get('destination')
        route.distance = request.POST.get('distance')
        route.image=request.FILES.get('image')
        route.estimated_time = request.POST.get('estimated_time')
        route.save()
        return redirect('route_list_add')

    return render(request, 'admin/edit_route.html', {'route': route})


def delete_route(request, id):
    route = get_object_or_404(Route, id=id)
    route.delete()
    return redirect('route_list_add')

   




# ======= Bus List of one Route ========
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
    
    Schedule.update_all_status()
    user=request.user
    transportation_company = getattr(user, "transportation_company", None)
    if request.method == "POST":
        try:
            # Get form data
            route_id = request.POST.get("route")
            bus_id = request.POST.get("bus")
            departure_input = request.POST.get("departure_time")
            arrival_input = request.POST.get("arrival_time")
            price = request.POST.get("price")

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
                arrival_time__gte=departure_time
            ).exists()

            if overlap_exists:
                messages.error(request, "A schedule already exists for this bus with overlapping times.")
                return redirect("schedule_list")

            # Create schedule
            Schedule.objects.create(
                route=route,
                bus=bus,
                available_seats=bus.total_seats,
                departure_time=departure_time,
                arrival_time=arrival_time,
                price=price,
                transportation_company=transportation_company
            )

            messages.success(request, "Schedule created successfully!")
            return redirect("schedule_list")

        except Exception as e:
            messages.error(request, f"Error creating schedule: {str(e)}")
            return redirect("schedule_list")


    selected_date_str = request.GET.get('date')
    search_query = request.GET.get('search', '').strip()
    time_range = request.GET.get('time_range', '').strip()
    print(time_range)

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()
        messages.warning(request, "Invalid date format, showing today's schedules")

    if transportation_company:
        
        schedules = Schedule.objects.filter(departure_time__date=selected_date,transportation_company=transportation_company)
    else:
        schedules=Schedule.objects.filter(departure_time__date=selected_date)
        
    if search_query:
        filters = Q(route__source__icontains=search_query) | \
                  Q(route__destination__icontains=search_query) | \
                  Q(bus__bus_number__icontains=search_query) | \
                  Q(price__icontains=search_query)
        if time_range:
            filters = Q(status=time_range)
            
        schedules = schedules.filter(filters).distinct()

    all_routes = Route.objects.all()
    transportation_company = getattr(request.user, "transportation_company", None)

    if transportation_company:
        all_buses = Bus.objects.filter(transportation_company=transportation_company)
    else:
        all_buses = Bus.objects.all()

   

    context = {
        'schedules': schedules,
        'all_routes': all_routes,
        'all_buses': all_buses,
        'selected_date': selected_date.isoformat(),
        'search_query': search_query,
    }

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
        bus=schedule.bus
        layout = get_object_or_404(SeatLayoutBooking, schedule=schedule)
    
        total_booked=bus.total_seats-schedule.available_seats
        
        
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
            'total_booked':total_booked,
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

    payments_query = Commission.objects.filter(bus__in=buses).order_by('-created_at')

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
    payment_paginator = Paginator(payments_query, payments_per_page)
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
        bus_payments = payments_query.filter(bus=bus)
        total_earning = bus_payments.aggregate(total=Sum('total_earnings'))['total'] or 0
        total_commission = bus_payments.aggregate(total=Sum('total_commission'))['total'] or 0
        net_earning = total_earning - total_commission
        total_trips = Schedule.objects.filter(status="finished", bus=bus).count()
        commission=bus.commission.filter(commission_type='bus').first()
   
        rate=commission.rate if commission else 0
        bus_earnings.append({
            'bus': bus,
            'rate':rate,
            'bus_number': bus.bus_number,
            'bus_type': bus.bus_type,
            'total_earning': total_earning,
            'total_commission': total_commission,
            'net_earning': net_earning,
            'total_trips': total_trips
        })


    bus_earnings.sort(key=lambda x: x['total_earning'], reverse=True)
    earnings_per_page = 5
    earnings_paginator = Paginator(bus_earnings, earnings_per_page)
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

    # Today's completed payments (for another view possibly)
    today = timezone.now().date()
    today_payments = Payment.objects.filter(
        payment_status="completed", 
        created_at__date=today
    ).order_by('-created_at')
    
    today_paginator = Paginator(today_payments, 10)
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
        'total_amount': total_amount,
        'total_commission': total_commission,
        'total_received': total_received,
        'total_trips': total_trips,
      
        'date_filter': date_filter,
    }

    return render(request, 'admin/bus_payment_details.html', context)





    # ==== Bus Seat Earning details ========
@login_required
def bus_earning_details(request, bus_id):
        bus = get_object_or_404(Bus, id=bus_id)

        # Get start and end date from request, default to None if not provided
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        payments = Payment.objects.filter(booking__bus=bus, payment_status='completed').order_by('-created_at')

        # If start_date and end_date are provided, convert them to timezone-aware datetimes and filter payments by date range
        if start_date and end_date:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))

            payments = payments.filter(created_at__gte=start_date, created_at__lte=end_date)

       

        earnings_list = []
        for payment in payments:
            schedule=payment.booking.schedule
            commission_obj=Commission.objects.get(schedule=schedule)
            
            commission_rate=commission_obj.rate
            commission = (payment.booking.schedule.price * commission_rate) / 100
            net_earning = payment.booking.schedule.price - commission

            passenger_name = payment.user.full_name
            transaction_id = payment.transaction_id
            

            earnings_list.append({
                'passenger': passenger_name,
                'amount_paid': payment.booking.schedule.price,
                'commission': commission,
                'commission_rate': commission_rate,
                'net_earning': net_earning,
                'payment_date': payment.created_at,
                'transaction_id': transaction_id,
                'booking_id':payment.booking.id
                
            })

        context = {
            'bus': bus,
            'earnings_list': earnings_list,
            
            'start_date': start_date.date() if start_date else None,
            'end_date': end_date.date() if end_date else None,
        }

        return render(request, 'admin/bus_earning_details.html', context)



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



def privacy(request):
    return render(request,'privacy.html')
    