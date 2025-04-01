from django.contrib.auth import authenticate
from django.db.models import Count
from datetime import datetime
import json
from rest_framework.viewsets import ModelViewSet

from custom_user.models import CustomUser,System,TransportationCompany
from route.models import Route, Schedule, Trip
from bus.models import Bus, TicketCounter,Driver,Staff,BusReservation,BusLayout,VechicleType
from booking.models import Commission, Booking,Payment,Rate,BusReservationBooking

from custom_user.serializers import CustomUserSerializer,SystemSerializer
from route.serializers import (
    RouteSerializer, ScheduleSerializer, BookingSerializer, TripSerializer, TicketCounterSerializer,
    BusSerializer,DriverSerializer,StaffSerializer,PaymentSerializer,CommissionSerializer,
    RateSerializer,BusReservationSerializer,VechicleTypeSerializer,VechicleReservationBookingSerializer,
    BusLayoutSerializer
)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status


   
        
# ====== admin dashboard Homedata =====
class AdminDashboardData(APIView):
    def get(self,request):
        try:
            data={}
            user_count=CustomUser.objects.filter(role="customer").count()
            bus_count=Bus.objects.filter(is_active=True).count()
            commission=Commission.objects.all()
            total_amount=0
            for i in commission:
                total_amount+=i.total_commission
            
            booking=Booking.objects.filter(booking_status="pending").count()
            trip=Trip.objects.filter(status="completed").count()
            booking_completed=Booking.objects.filter(booking_status='booked').count()
            data["total_revenue"]=total_amount
            data['total_booking_pending']=booking
            data['total_trip_completed']=trip
            data['ticket_booked']=booking_completed
            data["total_active_bus"]=bus_count
            data["total_user"]=user_count
            
            booking_obj=Booking.objects.all().order_by('-booked_at')[ :8]
            booking_serializer=BookingSerializer(booking_obj,many=True)
            
            trip=Trip.objects.all()[ :8]
            trip_serializer=TripSerializer(trip,many=True)
        
            return Response({'success':True,"data":data,"recent_booking":booking_serializer.data,"trip_data":trip_serializer.data},status=200)    
        
            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
        



# ========== Admin dashboard sidebar all views ==============


class AdminProfile(APIView):
    authentication_classes = [JWTAuthentication]
 
    def get(self, request):
        try:
            user = request.user
            serializer = CustomUserSerializer(user)
            return Response({"success": True, "data": serializer.data}, status=200)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
    
    def patch(self,request):
        try:
            user=request.user
            full_name=request.data.get('full_name')
            email=request.data.get('email')
            phone=request.data.get('phone')
            gender=request.data.get('gender')
            user.full_name=full_name
            user.email=email
            user.phone=phone
            user.gender=gender
            user.save()
            
            serializer=CustomUserSerializer(user)
            return Response({"success":True,"data":serializer.data,"message":"Data Updated Successfully"},status=200)
        except Exception as e:
            print(str(e))
            return Response({"success":True,"error":str(e)},status=400)


# ======= Ticket Counter  ===========
class TicketCounterView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            print(request.user)
            tickets = TicketCounter.objects.all().order_by('-created_at')
            serializer = TicketCounterSerializer(tickets, many=True)
            sub_admins=CustomUser.objects.filter(role='sub_admin')
            sub_admin_serializer=CustomUserSerializer(sub_admins,many=True)
            return Response({"success": True, "data": serializer.data,'sub_admins':sub_admin_serializer.data}, status=200)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

    def patch(self, request, id):
        try:
    
            # Fetch the TicketCounter instance based on ID
            ticket = TicketCounter.objects.get(id=id)
            user = ticket.user  # Get the related user object
            
            # Extract the data from the request
            counter_name = request.data.get('counter_name')
            location = request.data.get('location')
            
            # Correct way to access the nested 'user' data
            user_data = request.data.get('user', {})  # Safely extract the 'user' dictionary
            
            full_name = user_data.get('full_name')
            email = user_data.get('email')
            gender = user_data.get('gender')
            phone = user_data.get('phone')
            
            # Update the TicketCounter instance
            ticket.counter_name = counter_name
            ticket.location = location
            
            # Update the related user instance
            user.full_name = full_name
            user.email = email
            user.phone = phone
            user.gender = gender
            
            # Save the changes
            ticket.save()
            user.save()

            return Response({"success": True, "message": "Ticket Counter and User updated successfully"}, status=200)
        
        except Exception as e:
            # Handle any exceptions and return the error message
            return Response({"success": False, "error": str(e)}, status=400)

    
    def post(self, request):
        try:
            location = request.data.get('location')
            counter_name = request.data.get('counter_name')
            
            full_name = request.data.get('full_name')
            email = request.data.get('email')
            phone = request.data.get('phone')
            gender = request.data.get('gender')
            
            # Check if user already exists by email or phone
            if CustomUser.objects.filter(email=email).exists() or CustomUser.objects.filter(phone=phone).exists():
                return Response({"success": False, "message": "User already exists"}, status=400)
            
            # Create new CustomUser if no existing user
            user = CustomUser.objects.create(
                role='sub_admin',
                full_name=full_name,
                email=email,
                phone=phone,
                gender=gender
            )
            password=f"counter@123"
            user.set_password(password)
            user.save()

            # Create the TicketCounter
            TicketCounter.objects.create(
                counter_name=counter_name,
                user=user,
                location=location
            )
            
            return Response({"success": True, "message": "Counter added successfully"}, status=200)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

        
    def delete(self,request,id):
            try:
                ticket_obj=TicketCounter.objects.get(id=id)
                ticket_obj.delete()
                return Response({"success":True,"message":"Data deleted successfully"},status=200)
            except Exception as e:
                return Response({"success":False,"error":str(e)},status=400)
            
            
            

# ========= User Managemnet ==========
class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            users = CustomUser.objects.filter(role='customer')
            serializer = CustomUserSerializer(users, many=True)
            return Response({"success": True, "data": serializer.data}, status=200)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
        
    def post(self, request):
        try:
            email = request.data.get('email')  # You forgot to extract 'email'
            pass  # Implement your logic here
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
    
    def patch(self, request, *args, **kwargs):
        try:
            user_id = kwargs.get('id')  # Extract `id` from kwargs
            user = CustomUser.objects.get(id=user_id)
            
            full_name = request.data.get('full_name')
            email = request.data.get('email')
            phone = request.data.get('phone')
            gender = request.data.get('gender')
 
            user.full_name = full_name
            user.email = email
            user.phone = phone
            user.gender = gender
            user.save()

            return Response({"success": True, "message": "User data updated successfully"})
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
    
    def delete(self, request, *args, **kwargs):
        try:
            user_id = kwargs.get('id')  # Extract `id` from kwargs
            user = CustomUser.objects.get(id=user_id)
            user.delete()
            return Response({"success": True, "message": "User deleted successfully"}, status=200)
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)




# ======= Driver Management =========
class DriverListView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        try:
            user=request.user
            transportation_company = getattr(user, "transportation_company", None)
            drivers=Driver.objects.none()
            if transportation_company:
                drivers=Driver.objects.filter(transportation_company=transportation_company)
            else:
                drivers = Driver.objects.all()
            serializer = DriverSerializer(drivers, many=True)
            return Response({"success": True, "data": serializer.data}, status=200) 
            
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
        
    
    def post(self,request):
        try:
            user=request.user
            transportation_company = getattr(user, "transportation_company", None)
            
            full_name=request.data.get('full_name')
            driver_profile=request.FILES.get('driver_profile')
            license_image=request.FILES.get('license_image')
            phone_number=request.data.get('phone_number')
            if Driver.objects.filter(phone_number=phone_number).exists():
                return Response({"success":False,"message":"Driver already exists"},status=400)
            
            Driver.objects.create(full_name=full_name,
                                  driver_profile=driver_profile,
                                  license_image=license_image,
                                  phone_number=phone_number,
                                  transportation_company=transportation_company)
            return Response({"success":True,"message":"Driver added successfully"},status=200)
            
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
        
    def patch(self,request,*args,**kwargs):
        try:
            id=kwargs.get('id')
            driver=Driver.objects.get(id=id)
            full_name=request.data.get('full_name')
            driver_profile=request.FILES.get('driver_profile')
            license_image=request.FILES.get('license_image')
            phone_number=request.data.get('phone_number')
            
            driver.full_name=full_name
            driver.driver_profile=driver_profile
            driver.license_image=license_image
            driver.phone_number=phone_number
            driver.save()
            return Response({"success":True,"message":"Driver Updated Successfully"},status=200)
            
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
        
    def delete(self,request,*args,**kwargs):
        try:
            id=kwargs.get('id')
            driver=Driver.objects.get(id=id)
            driver.delete()
            return Response({"success":True,"message":"Driver deleted successfully"},status=200)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
        

# ======== Staff managment  ==========
class StaffListView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        try:
            user=request.user
            transportation_company = getattr(user, "transportation_company", None)
            staff=Staff.objects.none()
            if transportation_company:
                print(transportation_company)
                staff=Staff.objects.filter(transportation_company=transportation_company)
            else:
                print("NoTicketConter")
                staff=Staff.objects.all()
            serializer=StaffSerializer(staff,many=True)
            return Response({"success":True,"data":serializer.data},status=200)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
    
    
    def post(self,request):
        try:
            user=request.user
            transportation_company = getattr(user, "transportation_company", None)
            
            full_name=request.data.get('full_name')
            staff_profile=request.FILES.get('staff_profile')
            phone_number=request.data.get('phone_number')
            if Staff.objects.filter(phone_number=phone_number).exists():
                return Response({"success":False,"message":"Staff already exists"},status=400)
            Staff.objects.create(full_name=full_name,staff_profile=staff_profile,phone_number=phone_number,transportation_company=transportation_company)
            return Response({"success":True,"message":"Staff added successfully"},status=200)
        except Exception as e:
            return Response({'success':True,'error':str(e)},status=400)
    
    def patch(self,request,*args,**kwargs):
        try:
            id=kwargs.get('id')
            staff=Staff.objects.get(id=id)
            full_name=request.data.get('full_name')
            staff_profile=request.FILES.get('staff_profile')
            phone_number=request.data.get('phone_number')
            staff.full_name=full_name
            staff.staff_profile=staff_profile
            staff.phone_number=phone_number
            staff.save()
            return Response({'success':True,"message":"Staff Updated Successfully"},status=200)
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)

    def delete(self,request,*args,**kwargs):
        try:
            id=kwargs.get('id')
            staff=Staff.objects.get(id=id)
            staff.delete()
            return Response({'success':True,'message':"Staff deleted successfully"},status=200)
        
        except Exception as e:
            return Response({'success':True,'error':str(e)},status=400)
     
# ========= Bus Management ========
class BusListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            transportation_company = getattr(user, "transportation_company", None)

            # Filter buses based on ticket counter
            buses = Bus.objects.filter(transportation_company=transportation_company) if transportation_company else Bus.objects.all()

            # Get all routes
            routes = Route.objects.all()

            # Get drivers not assigned to any bus
            assigned_driver_ids = Bus.objects.filter(driver__isnull=False).values_list("driver__id", flat=True)
            unassigned_drivers = Driver.objects.exclude(id__in=assigned_driver_ids)

            # Get staff not assigned to any bus
            assigned_staff_ids = Bus.objects.filter(staff__isnull=False).values_list("staff__id", flat=True)
            unassigned_staff = Staff.objects.exclude(id__in=assigned_staff_ids)

            # Serialize data
            response_data = {
                "success": True,
                "data": BusSerializer(buses, many=True).data,
                "all_routes": RouteSerializer(routes, many=True).data,
                "all_drivers": DriverSerializer(unassigned_drivers, many=True).data,
                "all_staff": StaffSerializer(unassigned_staff, many=True).data,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            print(request.data)
            
            # Extract and validate transportation_company
            user = request.user
            transportation_company = getattr(user, "transportation_company", None)
            
            # Extract and validate driver
            driver_id = request.data.get('driver')
            driver_obj = None
            if driver_id:
                driver_obj = Driver.objects.get(id=driver_id)
                if Bus.objects.filter(driver=driver_obj).exists():
                    return Response({"success": False, "error": "Driver already assigned"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract and validate staff
            staff_id = request.data.get('staff')
            staff_obj = None
            if staff_id:
                staff_obj = Staff.objects.get(id=staff_id)
                if Bus.objects.filter(staff=staff_obj).exists():
                    return Response({"success": False, "error": "Staff already assigned"}, status=status.HTTP_400_BAD_REQUEST)

            # Extract and validate route
            route_id = request.data.get('route')
            route_obj = Route.objects.get(id=route_id)

            # Extract other fields
            bus_number = request.data.get('bus_number')
            bus_type = request.data.get('bus_type', 'deluxe_bus')
            bus_image = request.FILES.get('bus_image')
            
            # Parse JSON fields
            features = request.data.get('features', '[]')
            if isinstance(features, list):
                features = features[0]
            try:
                features = json.loads(features) if isinstance(features, str) else features
            except json.JSONDecodeError:
                return Response({"success": False, "error": "Invalid features format"}, status=status.HTTP_400_BAD_REQUEST)
            
            layout = request.data.get('layout', '{}')
            if isinstance(layout, list):
                layout = layout[0]
            try:
                layout = json.loads(layout) if isinstance(layout, str) else layout
            except json.JSONDecodeError:
                return Response({"success": False, "error": "Invalid layout format"}, status=status.HTTP_400_BAD_REQUEST)
            
            rows = layout.get('rows')
            columns = layout.get('columns')
            layout_data = layout.get('seatLayout')
            aisleAfterColumn = layout.get('aisleAfterColumn')
            
            # Extract total seats
            total_seats_list = request.data.getlist('total_seats')
            total_seats = int(total_seats_list[0]) if total_seats_list else 35
            
            # Convert boolean fields
            def str_to_bool(value):
                return str(value).lower() in ['true', '1', 'yes']
            
            is_active = str_to_bool(request.data.get('is_active'))
            is_running = str_to_bool(request.data.get('is_running'))
            
            # Create bus object with transportation_company
            bus = Bus.objects.create(
                driver=driver_obj,
                staff=staff_obj,
                bus_number=bus_number,
                bus_type=bus_type,
                features=features,
                bus_image=bus_image,
                total_seats=total_seats,
                available_seats=total_seats,
                route=route_obj,
                is_active=is_active,
                is_running=is_running,
                transportation_company=transportation_company  
            )
            
            # Create Bus layout
            BusLayout.objects.create(bus=bus, rows=rows, column=columns, layout_data=layout_data, aisle_column=aisleAfterColumn)
            
            # Serialize response
            bus_serializer = BusSerializer(bus)
            return Response({"success": True, "message": "Bus created successfully", "data": bus_serializer.data}, status=status.HTTP_201_CREATED)
        
        except (Driver.DoesNotExist, Staff.DoesNotExist, Route.DoesNotExist) as e:
            return Response({"success": False, "error": f"{e.__class__.__name__.replace('DoesNotExist', '')} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

    

    def patch(self, request, *args, **kwargs):
        try:
            print(request.data)
            bus_id = kwargs.get('id')
            bus = Bus.objects.get(id=bus_id)

            driver_id = request.data.get('driver')
            if driver_id:
                driver_obj = Driver.objects.get(id=driver_id)
                bus.driver = driver_obj 

            staff_id = request.data.get('staff')
            if staff_id:
                staff_obj = Staff.objects.get(id=staff_id)
                bus.staff = staff_obj

            
            bus_number = request.data.get('bus_number')
            bus.bus_number = bus_number

            bus_type = request.data.get('bus_type')
            bus.bus_type = bus_type
           
            features = request.data.get('features')
            if features:
                bus.features = json.loads(features)  # Convert JSON string to Python list
                
            bus_image = request.FILES.get('bus_image')
            if bus_image:
                bus.bus_image = bus_image

            # Convert total_seats to integer before updating
            total_seats=request.data.get('total_seats')
            if total_seats:
                try:
                    if isinstance(total_seats, list):  # If it's a list, take the first value
                        total_seats = total_seats[0]
                    bus.total_seats = int(total_seats)  # Convert from string to int
                except ValueError:
                    return Response({"success": False, "error": "Invalid total_seats value"}, status=status.HTTP_400_BAD_REQUEST)

            route_id = request.data.get('route')
            if route_id:
                bus.route = Route.objects.get(id=route_id)

            is_active = request.data.get('is_active')
            if is_active is not None:
                bus.is_active = is_active == 'true'

            is_running = request.data.get('is_running')
            if is_running is not None:
                bus.is_running = is_running == 'true'
                
            
            bus.save()
                
            bus_layout=BusLayout.objects.get(bus=bus)
            layout = request.data.get('layout')
            layout=json.loads(layout)
            
            bus_layout.rows=layout.get('rows')
            bus_layout.column=layout.get('columns')
            bus_layout.aisle_column=layout.get('aisleAfterColumn')
            bus_layout.layout_data=layout.get('seatLayout')
            bus_layout.save()
            
            return Response({
                "success": True,
                "message": "Bus updated successfully",
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        try:
            bus_id = kwargs.get('id')
            if not bus_id:
                return Response({"success": False, "error": "Bus ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
            bus = Bus.objects.get(id=bus_id)
            bus.delete()
            return Response({"success": True, "message": "Bus deleted successfully"}, status=status.HTTP_200_OK)
        
        except Bus.DoesNotExist:
            return Response({"success": False, "error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        




# ========= Schedule =========

class ScheduleView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            transportation_company = getattr(user, "transportation_company", None)
            schedules=Schedule.objects.none()
            if transportation_company:
                schedules=Schedule.objects.filter(transportation_company=transportation_company)
            else:
                schedules = Schedule.objects.all()
            # Fetch all schedules
            all_buses = Bus.objects.all()
            print(all_buses)
            assigned_bus_ids = Schedule.objects.values_list('bus_id', flat=True).distinct()
            unassigned_buses = all_buses.exclude(id__in=assigned_bus_ids)
            bus_serializer = BusSerializer(unassigned_buses, many=True)
            
            
            routes = Route.objects.all()
            schedule_serializer = ScheduleSerializer(schedules, many=True)
            route_serializer = RouteSerializer(routes, many=True)
            return Response({
                "success": True,
                "data": schedule_serializer.data,
                "all_route": route_serializer.data,
                "all_buses":bus_serializer.data
                
                
            }, status=status.HTTP_200_OK)

        except Exception as e:
           
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    def post(self,request):
        try:
            user = request.user
            transportation_company = getattr(user, "transportation_company", None)
            
            route_id=request.data.get('route')
            route_obj=Route.objects.get(id=route_id)
            
            bus_id=request.data.get('bus')
            bus_obj=Bus.objects.get(id=bus_id)
            departure=request.data.get('departure_time')
            arrival_time=request.data.get('arrival_time')
            price= request.data.get('price')
            
            Schedule.objects.create(bus=bus_obj,route=route_obj,departure_time=departure,arrival_time=arrival_time,price=price,transportation_company=transportation_company)
            return Response({"success":True,"message":"Schedule added successfully"})
        except Exception as e:
            return Response({'success':True,'error':str(e)},status=400)
    
    def patch(self,request,*args,**kwargs):
        try:
            
            schedule_id= kwargs.get('id')
            schedule=Schedule.objects.get(id=schedule_id)
            
            route_id=request.data.get('route')
            route_obj=Route.objects.get(id=route_id)
            
            bus_id=request.data.get('bus')
            bus_obj=Bus.objects.get(id=bus_id)
            
            departure=request.data.get('departure_time')
            arrival_time=request.data.get('arrival_time')
            price= request.data.get('price')
            
            schedule.bus=bus_obj
            schedule.route=route_obj
            schedule.departure_time=departure,
            schedule.arrival_time=arrival_time
            schedule.price=price
            schedule.save()
            return Response({'success':True,"message":"Schedule Updated Successfully"},status=200)
            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
        
    
    def delete(self,request,*args,**kwargs):
        try:
            id=kwargs.get('id')
            print(id)
            schedule=Schedule.objects.get(id=id)
            print(schedule)
            schedule.delete()
            return Response({"success":True,"message":"Schedule deleted Successfully"})            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
        


# ======= Bus  details schedule =========
class BusDetailsScheduleApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request,*args,**kwargs):
        try:
            bus_id=kwargs.get('id')
            bus_obj=Bus.objects.get(id=bus_id)
            serializer_bus=BusSerializer(bus_obj)
            
            
            layout_obj=BusLayout.objects.get(bus=bus_obj)
            schedule_obj=Schedule.objects.get(bus=bus_obj)
            booked_seat=bus_obj.total_seats-bus_obj.available_seats
            total_amount=schedule_obj.price*booked_seat
            serializer_layout=BusLayoutSerializer(layout_obj)
            
            booking=Booking.objects.filter(bus=bus_obj)
            serializer_booking=BookingSerializer(booking,many=True)
            
            return Response({'success':True,'bus_data':serializer_bus.data,"bus_layout":serializer_layout.data,"total_amount":total_amount,"booking_data":serializer_booking.data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
    
# =========== Routes Manangemnet ========

class RouteApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    
    def get(self,request):
        try:
            route=Route.objects.all()
            serializer=RouteSerializer(route,many=True)
            return Response({'success':True,'data':serializer.data},status=200)    
        
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
    def post(self,request):
        try:
            print(request.data)
            source=request.data.get('source')
            destination=request.data.get('destination')
            distance=request.data.get('distance')
            estimated_time=request.data.get('estimated_time')
            Route.objects.create(source=source,destination=destination,distance=distance,estimated_time=estimated_time)
            
            return Response({'success':True,'message':'Route added successfully'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
            
    
    def patch(self,request,*args,**kwargs):
        try:
            print(request.data)
            id=kwargs.get('id')
            route=Route.objects.get(id=id)
            source=request.data.get('source')
            destination=request.data.get('destination')
            distance=request.data.get('distance')
            
            route.destination=destination
            route.source=source
            route.distance=distance
            route.save()
            return Response({'success':True,'message':'Route data updated succesfully '})
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
            
    
    def delete(self,request,*args,**kwargs):
        try:
            
            id=kwargs.get('id')
            route=Route.objects.get(id=id)
            route.delete()
            return Response({'success':True,'message':"Route deleetd successfully "})
            
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)



# ======= Bus List of one Route ========
class RouteBusListAPiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request,*args,**kwargs):
        try:
            route_id=kwargs.get('id')
            route=Route.objects.get(id=route_id)
            bus_obj=Bus.objects.filter(schedule__route_id=route_id).distinct()
            total_bus=Bus.objects.filter(schedule__route_id=route_id).distinct().count()
            source=route.source
            destination=route.destination
            
            serializer=BusSerializer(bus_obj,many=True)
            return Response({'success':True,'data':serializer.data,"total_bus":total_bus,"source":source,"destination":destination},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
# ========== Booking Management  =================
class BookingAPiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        try:
            bus_reserve=BusReservationBooking.objects.all().order_by('-created_at')
            serializer_bus=VechicleReservationBookingSerializer(bus_reserve,many=True)
            
            booking=Booking.objects.all().order_by('-booked_at')
            serializer=BookingSerializer(booking,many=True)
            return Response({'success':True,'data':serializer.data,"bus_reserve":serializer_bus.data},status=200)
            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
    
    
    def patch(self,request,*args,**kwargs):
        try:
            print(request.data)
            id=kwargs.get('id')
            booking_obj=Booking.objects.get(id=id)
            
            booking_status=request.data.get('booking_status')
            booking_obj.booking_status=booking_status
            booking_obj.save()
            return Response({'success':True,'message':"Booking Status Updated Successfully"})
        except Exception as e:
            return Response({'success':True,'error':str(e)},status=400)
        

# ======= Bookinglist of one User ==============
class BookingScheduleOneUserDetails(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request,*args,**kwargs):
        try:
            booking_id=kwargs.get('id')
            booking_obj=Booking.objects.get(id=booking_id)
            print(booking_id)
            count=len(booking_obj.seat)
            total_price=count*booking_obj.schedule.price
            data = {    'user':booking_obj.user.full_name,
                        'user_phone':booking_obj.user.phone,
                        'bus_number': booking_obj.bus.bus_number,
                        'source': booking_obj.bus.route.source,
                        'destination': booking_obj.bus.route.destination,
                        'booking_status': booking_obj.booking_status,
                        'seat': booking_obj.seat,
                        'booked_at': booking_obj.booked_at,
                        'total_price': total_price,
                        'total_seat': count,
                        
            }
            return Response({'success':True,'data':data},status=200)
        
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)

# ======================
# Vehicle Reservation
# =======================

    
class VechicleReservationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user=request.user
            transportation_company=getattr(user,'transportation_company',None)
            bus_reserve = BusReservation.objects.none()
            if transportation_company:
                bus_reserve=BusReservation.objects.filter(transportation_company)
            else:
                bus_reserve = BusReservation.objects.all()
            serializer = BusReservationSerializer(bus_reserve, many=True)

            # Fetch drivers not assigned to any reservation
            assigned_driver_ids = BusReservation.objects.filter(driver__isnull=False).values_list('driver__id', flat=True)
            unassigned_drivers = Driver.objects.exclude(id__in=assigned_driver_ids)
            driver_serializer = DriverSerializer(unassigned_drivers, many=True)
            
            assigned_staff_ids = BusReservation.objects.filter(staff__isnull=False).values_list('staff__id', flat=True)
            unassigned_staff = Staff.objects.exclude(id__in=assigned_staff_ids)
            staff_serializer = StaffSerializer(unassigned_staff, many=True)

            vechicle_types = VechicleType.objects.all()
            vechicle_type_serializer = VechicleTypeSerializer(vechicle_types, many=True)

            return Response({
                'success': True,
                'data': serializer.data,
                'unassigned_drivers': driver_serializer.data,
                'unassigned_staff': staff_serializer.data,
                'vechicle_types': vechicle_type_serializer.data
            }, status=200)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

    def post(self, request):
        try:
            print(request.data)
            user=request.user
            transportation_company=getattr(user,'transportation_company',None)
            name = request.data.get('name')
            type_name = request.data.get('type')
            vechicle_number = request.data.get('vehicle_number')
            vechicle_model = request.data.get('vehicle_model')
            color = request.data.get('color')
            driver_name = request.data.get('driver_id')
            staff_name = request.data.get('staff_id')
            total_seats = request.data.get('total_seats', 35)
            price = request.data.get('price')

            # Validate and fetch related objects
            type_obj = VechicleType.objects.get(name=type_name) if type_name else None
            driver_obj = Driver.objects.get(full_name=driver_name) if driver_name else None
            staff_obj = Staff.objects.get(full_name=staff_name) if staff_name else None

            # Create the reservation
            reservation = BusReservation.objects.create(
                name=name,
                type=type_obj,
                vechicle_number=vechicle_number,
                vechicle_model=vechicle_model,
                color=color,
                driver=driver_obj,
                staff=staff_obj,
                total_seats=total_seats,
                price=price,
                transportation_company=transportation_company
            )

            serializer = BusReservationSerializer(reservation)
            return Response({'success': True, 'message': 'Reservation created successfully', 'data': serializer.data}, status=201)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)


    def patch(self, request, *args, **kwargs):
        try:
            print(request.data)
            reservation_id = kwargs.get('id')
            reservation = BusReservation.objects.get(id=reservation_id)

            name = request.data.get('name')
            type_name = request.data.get('type')
            vechicle_number = request.data.get('vehicle_number')
            vechicle_model = request.data.get('vehicle_model')
            color = request.data.get('color')
            driver_name = request.data.get('driver_id')
            staff_name = request.data.get('staff_id')
            total_seats = request.data.get('total_seats')
            price = request.data.get('price')

            # Update fields if provided
            if name:
                reservation.name = name
            if type_name:
                reservation.type = VechicleType.objects.get(name=type_name)
            if vechicle_number:
                reservation.vechicle_number = vechicle_number
            if vechicle_model:
                reservation.vechicle_model = vechicle_model
            if color:
                reservation.color = color
            if driver_name:
                reservation.driver = Driver.objects.get(full_name=driver_name)
            if staff_name:
                reservation.staff = Staff.objects.get(full_name=staff_name)
            if total_seats:
                reservation.total_seats = total_seats
            if price:
                reservation.price = price

            reservation.save()
            serializer = BusReservationSerializer(reservation)
            return Response({'success': True, 'message': 'Reservation updated successfully', 'data': serializer.data}, status=200)
        except BusReservation.DoesNotExist:
            return Response({'success': False, 'message': 'Reservation not found'}, status=404)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

    def delete(self, request, *args, **kwargs):
        try:
            reservation_id = kwargs.get('id')
            reservation = BusReservation.objects.get(id=reservation_id)
            reservation.delete()
            return Response({'success': True, 'message': 'Reservation deleted successfully'}, status=200)
        except BusReservation.DoesNotExist:
            return Response({'success': False, 'message': 'Reservation not found'}, status=404)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

# ================
# Vehicle Type
# ===================
class VehicleTypeViewSet(ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = VechicleType.objects.all()
    serializer_class = VechicleTypeSerializer
        

#========= Payment and Commission =============
class PaymentApiView(APIView):
    
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self, request):
        try:
            payment = Payment.objects.all().order_by('-created_at')
            serializer_payment = PaymentSerializer(payment, many=True)
            commission = Commission.objects.all()
            serializer_commission = CommissionSerializer(commission, many=True)
            rate = Rate.objects.first()
            serializer_rate = RateSerializer(rate)
            
            return Response({
                'success': True,
                'payment_data': serializer_payment.data,
                'commission_data': serializer_commission.data,
                'rate_data': serializer_rate.data
            }, status=200)
        
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

#   ======= Rate ============

class RateApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def patch(self,request,*args,**kwargs):
        try:
            print(request.data)
            id=kwargs.get('id')
            rate=request.data.get('rate')
            rate_obj = Rate.objects.get(id=id)
            rate_obj.rate=rate
            return Response({'success':True,'message':'Commission Rate Updated Successfully'},status=200)
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
from django.db.models import Sum, Count, F
from django.utils.timezone import now


# ========== Report and analysis =========
class ReportAnalysisApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Optional: Restrict access to logged-in admins

    def get(self, request):
        month, year = now().month, now().year  # Get current month & year
        
        # 1️ Monthly Revenue & Commission
        monthly_revenue = Payment.objects.filter(created_at__month=month, created_at__year=year).aggregate(total=Sum('price'))['total'] or 0
        monthly_commission = Payment.objects.filter(created_at__month=month, created_at__year=year).aggregate(total=Sum('commission_deducted'))['total'] or 0

        # 2️ Monthly Bookings & Cancellations
        total_bookings = Booking.objects.filter(booked_at__month=month, booked_at__year=year).count()
        canceled_bookings = Booking.objects.filter(booked_at__month=month, booked_at__year=year, booking_status='canceled').count()

        # 3️ Top Performing Buses
        top_buses = Booking.objects.values(bus_number=F('bus__bus_number')) \
            .annotate(total_bookings=Count('id')) \
            .order_by('-total_bookings')[:5]

        # 4️ Top Active Customers
        top_customers = Booking.objects.values(customer=F('user__full_name')) \
            .annotate(total_bookings=Count('id')) \
            .order_by('-total_bookings')[:5]

        return Response({
            "success":True,
            "month": f"{month}-{year}",
            "monthly_revenue": monthly_revenue,
            "monthly_commission": monthly_commission,
            "monthly_bookings": total_bookings,
            "monthly_canceled": canceled_bookings,
            "top_buses": list(top_buses),
            "top_customers": list(top_customers)
        }) 





# ========================
# Settings 
#=========================

class SettingsApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        system=System.objects.all().first()
        serializer=SystemSerializer(system)
        return Response({"success":True,"data":serializer.data},status=200)
    
    
    def patch(self,request,*args,**kwargs):
        try:
            print(request.data)
            id=kwargs.get('id')
            system=System.objects.get(id=id)
            name=request.data.get('name')
            email=request.data.get('email')
            phone=request.data.get('phone')
            image=request.FILES.get('image')
            address=request.data.get('address')
            
            system.name=name
            system.email=email
            system.phone=phone
            system.image=image
            system.address=address
            system.save()
            return Response({"success":True,'message':"System data upated successfully"},status=201)
        
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)
        
        
        