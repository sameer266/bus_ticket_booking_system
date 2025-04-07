from django.contrib.auth import authenticate
from django.db.models import Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Count, Sum,F


import json
from rest_framework.viewsets import ModelViewSet

from custom_user.models import CustomUser,System,TransportationCompany
from route.models import Route, Schedule, Trip
from bus.models import Bus, TicketCounter,Driver,Staff,BusReservation,BusLayout,VechicleType
from booking.models import Commission, Booking,Payment,Rate,BusReservationBooking

from custom_user.serializers import CustomUserSerializer,SystemSerializer
from route.serializers import (
    BusSerializer,VechicleTypeSerializer,
   
)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status


   
        
def is_admin(user):
    return user.is_authenticated and user.role == "admin"

def is_subadmin(user):
    return user.is_authenticated and user.role=="sub_admin"

@login_required
# @user_passes_test(is_admin,is_subadmin)
def admin_dashboard(request):
        """
        Render the admin dashboard with overview statistics and recent data
        """
  
        # Gather stats data
        data = {}
        user_count = CustomUser.objects.filter(role="customer").count()
        bus_count = Bus.objects.filter(is_active=True).count()
        
        # Calculate total commission
        commissions = Commission.objects.all()
        total_amount = sum(commission.total_commission for commission in commissions)
        
        # Get booking and trip counts
        pending_bookings = Booking.objects.filter(booking_status="pending").count()
        completed_trips = Trip.objects.filter(status="completed").count()
        booked_tickets = Booking.objects.filter(booking_status='booked').count()
        
        # Build data dictionary
        data["total_revenue"] = total_amount
        data['total_booking_pending'] = pending_bookings
        data['total_trip_completed'] = completed_trips
        data['ticket_booked'] = booked_tickets
        data["total_active_bus"] = bus_count
        data["total_user"] = user_count
        
        # Get recent bookings and trips
        recent_booking = Booking.objects.all().order_by('-booked_at')[:8]
        trip_data = Trip.objects.all()[:8]
        
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
def ticket_counter_list(request):
    counters = TicketCounter.objects.all().order_by('-created_at')
    sub_admins = CustomUser.objects.filter(role='sub_admin')

    if request.method == "POST":
        # Get data from the request
        counter_name = request.POST.get('counter_name')
        location = request.POST.get('location')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists() or CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, "User already exists!")
        else:
            # Create a new CustomUser
            user = CustomUser.objects.create(
                role='sub_admin',
                full_name=full_name,
                email=email,
                phone=phone,
                gender=gender
            )
            user.set_password("counter@123")  # Default Password
            user.save()

            # Create the TicketCounter
            TicketCounter.objects.create(
                counter_name=counter_name,
                user=user,
                location=location
            )

            messages.success(request, "Ticket Counter added successfully!")
            return redirect("ticket_counter_list")

    return render(request, "admin/ticket_counter.html", {
        "counters": counters,
        "sub_admins": sub_admins,
    })


@login_required
def edit_ticket_counter(request, id):
    ticket_counter = get_object_or_404(TicketCounter, id=id)
    user = ticket_counter.user

    if request.method == "POST":
        # Get updated data from the request
        ticket_counter.counter_name = request.POST.get('counter_name')
        ticket_counter.bank_name=request.POST.get('bank_name')
        ticket_counter.bank_account=request.POST.get('bank_account')
        ticket_counter.location = request.POST.get('location')

        user.full_name = request.POST.get('full_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.gender = request.POST.get('gender')

        # Save updated data
        ticket_counter.save()
        user.save()

        messages.success(request, "Ticket Counter updated successfully!")
        return redirect("ticket_counter_list")

    return render(request, "admin/edit_ticket_counter.html", {
        "ticket_counter": ticket_counter,
        "user": user,
    })


@login_required
def delete_ticket_counter(request, id):
    ticket_counter = get_object_or_404(TicketCounter, id=id)
    user = ticket_counter.user
    user.delete()  
    ticket_counter.delete()

    messages.success(request, "Ticket Counter deleted successfully!")
    return redirect("ticket_counter_list")


# ========= Sub Admin Bus List ==========
@login_required
def sub_admin_bus_list(request,id):
    user = TransportationCompany.objects.filter(id=id).first()
    buses = Bus.objects.filter(transportation_company=user)
    bus_schedules = Schedule.objects.filter(bus__in=buses).values('bus__id').annotate()
    bus_count = buses.count()
    bus_schedule_count = Schedule.objects.filter(bus__in=buses).count()

    paginator = Paginator(buses, 10)
    page_number = request.GET.get('page')
    buses_page = paginator.get_page(page_number)

    context = {
        'buses': buses_page,
        'bus_schedules': bus_schedules,
        'bus_count': bus_count,
        'bus_schedule_count': bus_schedule_count,
    }
    return render(request, 'admin/sub_admin_bus_list.html', context)
            

# ========= User Managemnet ==========
@login_required
def manage_users(request):
    """List and add users from the same template."""
    users = CustomUser.objects.filter(role='customer')

    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')

        if  CustomUser.objects.filter(phone=phone).exists():
            messages.error(request,"Phone number already exists")

        user = CustomUser.objects.create(
            role='customer',
            full_name=full_name,
            email=email,
            phone=phone,
            gender=gender
        )
        user.set_password("counter@123")
        user.save()
        return redirect('manage_users')  # Reload page after adding user

    return render(request, 'admin/manage_users.html', {'users': users})


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

            Driver.objects.create(
                full_name=full_name,
                phone_number=phone_number,
                driver_profile=driver_profile,
                license_image=license_image,
                transportation_company=request.user.transportation_company
            )
            return redirect('manage_driver_and_staff')  # Reload page after adding driver

        # Handle Staff Add
        elif 'add_staff' in request.POST:
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            staff_profile = request.FILES.get('staff_profile')
            transportation_company = request.user.transportation_company

            if Staff.objects.filter(phone_number=phone_number).exists():
                messages.error(request, "Staff already exists!")
                return redirect('manage_driver_and_staff')

            Staff.objects.create(
                full_name=full_name,
                staff_profile=staff_profile,
                phone_number=phone_number,
                transportation_company=transportation_company
            )
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
    transportation_company = getattr(user, "transportation_company", None)

    buses = Bus.objects.filter(transportation_company=transportation_company) if transportation_company else Bus.objects.all()
    routes = Route.objects.all()

    assigned_driver_ids = Bus.objects.filter(driver__isnull=False).values_list("driver__id", flat=True)
    unassigned_drivers = Driver.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_driver_ids)

    assigned_staff_ids = Bus.objects.filter(staff__isnull=False).values_list("staff__id", flat=True)
    unassigned_staff = Staff.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_staff_ids)

    context = {
        'buses': buses,
        'all_routes': routes,
        'all_drivers': unassigned_drivers,
        'all_staff': unassigned_staff,
        'bus_types': Bus.VEHICLE_CHOICES,
        'FEATURE_CHOICES': Bus.FEATURE_CHOICES  # Make sure this is passed
    }

    return render(request, 'admin/manage_bus.html', context)


@login_required
def create_bus(request):
    try:
        print(request.POST)
        # Extract form data
        bus_number = request.POST.get('bus_number')
        bus_type = request.POST.get('bus_type')
        driver_id = request.POST.get('driver')
        staff_id = request.POST.get('staff')
        route_id = request.POST.get('route')
        total_seats = int(request.POST.get('total_seats', 0))
        is_active = request.POST.get('is_active') == 'on'
        is_running = request.POST.get('is_running') == 'on'
        features = request.POST.get('features', '[]')
        bus_image = request.FILES.get('bus_image')

        # Get related objects
        driver = Driver.objects.get(id=driver_id) if driver_id else None
        staff = Staff.objects.get(id=staff_id) if staff_id else None
        route = Route.objects.get(id=route_id)

        # Create bus
        bus = Bus.objects.create(
            bus_number=bus_number,
            bus_type=bus_type,
            driver=driver,
            staff=staff,
            route=route,
            total_seats=total_seats,
            available_seats=total_seats,
            is_active=is_active,
            is_running=is_running,
            features=json.loads(features) if isinstance(features, str) else features,
            bus_image=bus_image,
            transportation_company=getattr(request.user, "transportation_company", None)
        )

        # Create Bus layout if layout data is provided
        layout = request.POST.get('layout', '{}')
        try:
            layout_data = json.loads(layout) if isinstance(layout, str) else layout
            rows = layout_data.get('rows')
            columns = layout_data.get('columns')
            seat_layout = layout_data.get('seatLayout')
            aisle_column = layout_data.get('aisleAfterColumn')

            if rows and columns and seat_layout:
                BusLayout.objects.create(
                    bus=bus,
                    rows=rows,
                    column=columns,
                    layout_data=seat_layout,
                    aisle_column=aisle_column
                )
        except json.JSONDecodeError:
            pass  # Handle invalid layout format silently

        return redirect('bus_list')
    except Exception as e:
        # Handle errors and redisplay form
        routes = Route.objects.all()
        drivers = Driver.objects.filter(transportation_company=getattr(request.user, "transportation_company", None))
        staff = Staff.objects.filter(transportation_company=getattr(request.user, "transportation_company", None))

        context = {
            'error': str(e),
            'bus_number': request.POST.get('bus_number'),
            'bus_type': request.POST.get('bus_type'),
            'selected_driver': request.POST.get('driver'),
            'selected_staff': request.POST.get('staff'),
            'selected_route': request.POST.get('route'),
            'total_seats': request.POST.get('total_seats'),
            'is_active': request.POST.get('is_active') == 'on',
            'is_running': request.POST.get('is_running') == 'on',
            'features': request.POST.get('features'),
            'all_routes': routes,
            'all_drivers': drivers,
            'all_staff': staff,
            'bus_types': Bus.VEHICLE_CHOICES,
            'features': Bus.FEATURE_CHOICES
        }
        return render(request, 'admin/manage_bus.html', context)
    
    
# ======= Edit bus ===========
from django.core.exceptions import ValidationError
@login_required
def edit_bus(request, bus_id):
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
            
            # Handle route
            route_id = request.POST.get('route')
            if route_id:
                bus.route = Route.objects.get(id=route_id)
            
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
        'route': bus.route.id if bus.route else None,
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
    if request.method == 'POST':
        bus.delete()
        return redirect('bus_list')
    return render(request, 'admin/bus_confirm_delete.html', {'bus': bus})





from django.core.serializers.json import DjangoJSONEncoder
# ======================
# Vehicle Reservation (Django Template View)
# =======================
@login_required
def vehicle_reservation(request, id=None):
    """
    Handles GET (list), POST (create/update/delete) requests for vehicle reservations.
    """
    user = request.user
    transportation_company = getattr(user, 'transportation_company', None)

    # Common context data
    reservations = BusReservation.objects.none()
    if transportation_company:
        reservations = BusReservation.objects.filter(transportation_company=transportation_company)
    else:
        reservations = BusReservation.objects.all()

    assigned_driver_ids = BusReservation.objects.filter(driver__isnull=False).values_list('driver__id', flat=True)
    unassigned_drivers = Driver.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_driver_ids)

    assigned_staff_ids = BusReservation.objects.filter(staff__isnull=False).values_list('staff__id', flat=True)
    unassigned_staff = Staff.objects.filter(transportation_company=transportation_company).exclude(id__in=assigned_staff_ids)

    vechicle_types = VechicleType.objects.all()

    # Prepare JSON data for each reservation
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
            # Note: image and document are file fields, so we'll skip their full paths here
        } for r in reservations
    ], cls=DjangoJSONEncoder)

    context = {
        'reservations': reservations,
        'unassigned_drivers': unassigned_drivers,
        'unassigned_staff': unassigned_staff,
        'vechicle_types': vechicle_types,
        'reservation_json': reservation_json,
    }

    if request.method == 'POST':
        if id:  # Update or Delete
            reservation = get_object_or_404(BusReservation, id=id)
            try:
                if 'delete_reservation' in request.POST:
                    reservation.delete()
                    return redirect('vehicle-reservation')

                # Update reservation
                reservation.name = request.POST.get('name', reservation.name)
                type_id = request.POST.get('type')
                if type_id:
                    reservation.type = VechicleType.objects.get(id=type_id)

                reservation.vechicle_number = request.POST.get('vechicle_number', reservation.vechicle_number)
                reservation.vechicle_model = request.POST.get('vechicle_model', reservation.vechicle_model)
                if 'image' in request.FILES:
                    reservation.image = request.FILES['image']
                if 'document' in request.FILES:
                    reservation.document = request.FILES['document']
                reservation.color = request.POST.get('color', reservation.color)

                driver_id = request.POST.get('driver_id')
                reservation.driver = Driver.objects.get(id=driver_id) if driver_id else None

                staff_id = request.POST.get('staff_id')
                reservation.staff = Staff.objects.get(id=staff_id) if staff_id else None

                reservation.total_seats = request.POST.get('total_seats', reservation.total_seats)
                reservation.price = request.POST.get('price', reservation.price)

                reservation.save()
                return redirect('vehicle-reservation')
            except Exception as e:
                print(f"Error updating reservation: {str(e)}")
                context['error'] = str(e)
                context['reservation'] = reservation

        elif 'add_reservation' in request.POST:  # Create
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

                type_obj = VechicleType.objects.get(id=type_id) if type_id else None
                driver_obj = Driver.objects.get(id=driver_id) if driver_id else None
                staff_obj = Staff.objects.get(id=staff_id) if staff_id else None

                BusReservation.objects.create(
                    name=name,
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
                return redirect('vehicle-reservation')
            except Exception as e:
                print(f"Error creating reservation: {str(e)}")
                context['error'] = str(e)

    # GET request: Render the list
    return render(request, 'admin/manage_reservation.html', context)




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
            vehicle_type.vehicle_count = 0
    
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
        return redirect('vechicle_type_list')

    return render(request, 'admin/edit_vechicle_type.html', {'vechicle_type': vechicle_type})   


@login_required
def delete_vechicle_type(request, id):
    vechicle_type = get_object_or_404(VechicleType, id=id)
    if request.method == 'POST':
        vechicle_type.delete()
        messages.success(request, "Vehicle type deleted successfully!")
        return redirect('vechicle_type_list')

    return render(request, 'admin/delete_vechicle_type.html', {'vechicle_type': vechicle_type})


# =============
#   Route
# ============

def route_list_and_add(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        distance = request.POST.get('distance')
        estimated_time = request.POST.get('estimated_time')

        if source and destination and distance and estimated_time:
            Route.objects.create(
                source=source,
                destination=destination,
                distance=distance,
                estimated_time=estimated_time
            )
            return redirect('route_list_add')  # Redirect to avoid form resubmission

    routes = Route.objects.all()
    return render(request, 'admin/manage_routes.html', {'routes': routes})



def edit_route(request, id):
    route = get_object_or_404(Route, id=id)

    if request.method == 'POST':
        route.source = request.POST.get('source')
        route.destination = request.POST.get('destination')
        route.distance = request.POST.get('distance')
        route.estimated_time = request.POST.get('estimated_time')
        route.save()
        return redirect('route_list')

    return render(request, 'admin/edit_route.html', {'route': route})


def delete_route(request, id):
    route = get_object_or_404(Route, id=id)
    if request.method == 'POST':
        route.delete()
        return redirect('route_list')

    return render(request, 'delete_route.html', {'route': route})




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
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Bus.DoesNotExist:
            return Response({"error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)

# ========= Schedule =========
def schedule_list(request):
    
    if request.method == "POST":
        route_id = request.POST.get("route")
        bus_id = request.POST.get("bus")
        departure_time = request.POST.get("departure_time")
        arrival_time = request.POST.get("arrival_time")
        price = request.POST.get("price")

        route = Route.objects.get(id=route_id)
        bus = Bus.objects.get(id=bus_id)

        Schedule.objects.create(route=route, bus=bus, departure_time=departure_time, arrival_time=arrival_time, price=price)
        return redirect("schedule_list")

    schedules = Schedule.objects.all()
    all_routes = Route.objects.all()
    all_buses = Bus.objects.none()
    transportation_company = getattr(request.user, "transportation_company", None)
    if transportation_company:
        all_buses = Bus.objects.filter(transportation_company=transportation_company)
    else:
        all_buses = Bus.objects.all()

    return render(request, "admin/manage_schedule.html", {
        "schedules": schedules,
        "all_routes": all_routes,
        "all_buses": all_buses
    })

def schedule_edit(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    
    if request.method == "POST":
        schedule.route = Route.objects.get(id=request.POST.get("route"))
        schedule.bus = Bus.objects.get(id=request.POST.get("bus"))
        schedule.departure_time = request.POST.get("departure_time")
        schedule.arrival_time = request.POST.get("arrival_time")
        schedule.price = request.POST.get("price")
        schedule.save()
        return redirect("schedule_list")

    all_routes = Route.objects.all()
    all_buses = Bus.objects.all()
    
    return render(request, "admin/manage_schedule.html", {
        "schedule": schedule,
        "all_routes": all_routes,
        "all_buses": all_buses
    })

def schedule_delete(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    schedule.delete()
    return redirect("schedule_list")






# ======= Bus  details schedule =========
def schedule_bus_details(request, id):
    bus = get_object_or_404(Bus, id=id)
    layout = get_object_or_404(BusLayout, bus=bus)
    schedule = get_object_or_404(Schedule, bus=bus)
    
    seat_layout_with_bookings = []
    booked_seats = {}
    booked_seat = 0
    
    for booking in Booking.objects.filter(bus=bus):
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
    })

# ======= Bookinglist of one User ==============
def booking_details(request, id):
    booking = get_object_or_404(Booking, id=id)
    count = len(booking.seat)
    total_price = count * booking.schedule.price
    
    data = {
        'user': booking.user.full_name,
        'user_phone': booking.user.phone,
        'bus_number': booking.bus.bus_number,
        'source': booking.bus.route.source,
        'destination': booking.bus.route.destination,
        'booking_status': booking.booking_status,
        'seat': booking.seat,
        'booked_at': booking.booked_at,
        'total_price': total_price,
        'total_seat': count,
    }
    
    return JsonResponse(data)

        


# ========== Booking Management  =================
def booking_management(request):
    try:
        # Fetch all bus reservations
        bus_reserve_data = BusReservationBooking.objects.all().order_by('-created_at')
        # Paginate the bus reservation data
        bus_reserve_paginator = Paginator(bus_reserve_data, 8)  # 8 items per page
        page_number_bus_reserve = request.GET.get('page')
        bus_reserve_page = bus_reserve_paginator.get_page(page_number_bus_reserve)

        # Fetch all bookings
        booking_data = Booking.objects.all().order_by('-booked_at')
        # Paginate the booking data
        booking_paginator = Paginator(booking_data, 10)  # 10 items per page
        page_number_booking = request.GET.get('page')
        booking_page = booking_paginator.get_page(page_number_booking)

        return render(request, 'admin/manage_booking.html', {
            'bus_reserve_data': bus_reserve_page,
            'booking_data': booking_page,
        })
    except Exception as e:
        return render(request, 'admin/manage_booking.html', {'error': str(e)})

    
    
# ========== Reports details  ===========

def report_analysis_view(request):
    current_month, current_year = now().month, now().year
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1

    # Current Month Data
    monthly_revenue = Payment.objects.filter(created_at__month=current_month, created_at__year=current_year).aggregate(total=Sum('price'))['total'] or 0
    monthly_commission = Payment.objects.filter(created_at__month=current_month, created_at__year=current_year).aggregate(total=Sum('commission_deducted'))['total'] or 0
    total_bookings = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year).count()
    canceled_bookings = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year, booking_status='canceled').count()
    top_buses = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year).values(bus_number=F('bus__bus_number')).annotate(total_bookings=Count('id')).order_by('-total_bookings')[:5]
    top_customers = Booking.objects.filter(booked_at__month=current_month, booked_at__year=current_year).values(customer=F('user__full_name')).annotate(total_bookings=Count('id')).order_by('-total_bookings')[:5]

    # Previous Month Data (for comparison)
    prev_revenue = Payment.objects.filter(created_at__month=prev_month, created_at__year=prev_year).aggregate(total=Sum('price'))['total'] or 0
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


    
 

#========= Payment and Commission =============
#========= Payment and Commission =============
@login_required
def payment_details(request):
    # Get the user's transportation company
    user_company = getattr(request.user, 'transpotation_company', None)
    
    # Get payments based on user's company
    payments = Payment.objects.filter(payment_status='completed')
    if user_company:
        # Filter payments to only include buses from user's company
        payments = payments.filter(bus__transpotation_company=user_company)
    
    # Order payments by date
    payments = payments.order_by('-created_at')
    
    # Get commission rate
    rate = Rate.objects.first()
    
    # Calculate totals
    total_payments = payments.aggregate(
        total_amount=Sum('price'),
        total_commission=Sum('commission_deducted')
    )
    
    total_received = (total_payments['total_amount'] or 0) - (total_payments['total_commission'] or 0)
    
    # Calculate per-bus statistics
    bus_stats = Payment.objects.filter(payment_status='completed')
    if user_company:
        bus_stats = bus_stats.filter(bus__transpotation_company=user_company)
    
    bus_stats = bus_stats.values(
        'bus__id', 
        'bus__bus_number',
        'bus__route__source',
        'bus__route__destination'
    ).annotate(
        total_earnings=Sum('price'),
        total_commission=Sum('commission_deducted'),
        payment_count=Count('id')
    ).order_by('-total_earnings')
    
    context = {
        'payments': payments,
        'rate': rate,
        'total_amount': total_payments['total_amount'] or 0,
        'total_commission': total_payments['total_commission'] or 0,
        'total_received': total_received,
        'bus_stats': bus_stats,
    }
    return render(request, 'admin/payment_details.html', context)

@login_required
def update_rate(request):
    rate = Rate.objects.first()
    
    if request.method == "POST":
        new_rate = request.POST.get('rate')
        if new_rate:
            rate.rate = new_rate
            rate.save()
            return redirect('payments_details')  # Redirect back to payment page

    return render(request, 'admin/payment_details.html', {'rate': rate})

        



# ================
# Vehicle Type
# ===================
class VehicleTypeViewSet(ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = VechicleType.objects.all()
    serializer_class = VechicleTypeSerializer
       