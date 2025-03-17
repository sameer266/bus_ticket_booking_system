from django.contrib.auth import authenticate
from django.db.models import Count
from datetime import datetime
import json

from custom_user.models import CustomUser, UserOtp
from route.models import Route, Schedule, Trip, CustomerReview
from bus.models import Bus, TicketCounter,Driver,Staff
from booking.models import Commission, Booking

from custom_user.serializers import CustomUserSerializer
from route.serializers import (
    RouteSerializer, ScheduleSerializer, CustomReviewSerializer, 
    BusScheduleSerializer, BookingSerializer, TripSerilaizer, TicketCounterSerializer,
    BusSerializer,DriverSerializer,StaffSerializer
)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status

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


# ========= Bus Management ========

class BusListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get all buses
            bus = Bus.objects.all()

            # Get all routes
            route = Route.objects.all()

            # Get drivers not assigned to any bus
            assigned_driver_ids = Bus.objects.filter(driver__isnull=False).values_list('driver__id', flat=True)
            unassigned_drivers = Driver.objects.exclude(id__in=assigned_driver_ids)

            # Get staff not assigned to any bus
            assigned_staff_ids = Bus.objects.filter(staff__isnull=False).values_list('staff__id', flat=True)
            unassigned_staff = Staff.objects.exclude(id__in=assigned_staff_ids)

            # Serialize the data
            route_serializer = RouteSerializer(route, many=True)
            driver_serializer = DriverSerializer(unassigned_drivers, many=True)
            staff_serializer = StaffSerializer(unassigned_staff, many=True)
            bus_serializer = BusSerializer(bus, many=True)

            # Return the response
            return Response({
                "success": True,
                "data": bus_serializer.data,
                "all_route": route_serializer.data,
                "all_driver": driver_serializer.data,
                "all_staff": staff_serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
          
            driver_id = request.data.get('driver')
            if driver_id:
                driver_obj = Driver.objects.get(id=driver_id)
                if Bus.objects.filter(driver=driver_obj).exists():
                    return Response({"success": False, "error": "Driver already assigned"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                driver_obj = None

            # Fetch staff and check if already assigned
            staff_id = request.data.get('staff')
            if staff_id:
                staff_obj = Staff.objects.get(id=staff_id)
                if Bus.objects.filter(staff=staff_obj).exists():
                    return Response({"success": False, "error": "Staff already assigned"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                staff_obj = None

            # Fetch route
            route_id = request.data.get('route')
            route_obj = Route.objects.get(id=route_id)

            # Get other fields
            bus_number = request.data.get('bus_number')
            bus_type = request.data.get('bus_type', 'deluxe_bus')  # Default from model
            features = request.data.get('features', [])  # Expecting a list
            features = json.loads(features)
            bus_image = request.FILES.get('bus_image')
            total_seats = request.data.get('total_seats', 35)  # Default from model
            is_active = request.data.get('is_active', False) == 'true'  # Convert string to boolean
            is_running = request.data.get('is_running', False) == 'true'  # Convert string to boolean

            # Create the bus
            bus = Bus.objects.create(
                driver=driver_obj,
                staff=staff_obj,
                bus_number=bus_number,
                bus_type=bus_type,
                features=features,
                bus_image=bus_image,
                total_seats=total_seats,
                available_seats=total_seats,  # Match total_seats initially
                route=route_obj,
                is_active=is_active,
                is_running=is_running
            )

            # Serialize the created bus for response
            bus_serializer = BusSerializer(bus)
            return Response({
                "success": True,
                "message": "Bus created successfully",
                "data": bus_serializer.data
            }, status=status.HTTP_201_CREATED)

        except Driver.DoesNotExist:
            return Response({"success": False, "error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
        except Staff.DoesNotExist:
            return Response({"success": False, "error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)
        except Route.DoesNotExist:
            return Response({"success": False, "error": "Route not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    

    def patch(self, request, *args, **kwargs):
        try:
          
            bus_id = kwargs.get('id')
            bus = Bus.objects.get(id=bus_id)

            driver_id = request.data.get('driver')
            if driver_id:
                driver_obj = Driver.objects.get(id=driver_id)
                if Bus.objects.filter(driver=driver_obj).exclude(id=bus_id).exists():
                    return Response({"success": False, "error": "Driver already assigned to another bus"}, status=status.HTTP_400_BAD_REQUEST)
                bus.driver = driver_obj

            staff_id = request.data.get('staff')
            if staff_id:
                staff_obj = Staff.objects.get(id=staff_id)
                if Bus.objects.filter(staff=staff_obj).exclude(id=bus_id).exists():
                    return Response({"success": False, "error": "Staff already assigned to another bus"}, status=status.HTTP_400_BAD_REQUEST)
                bus.staff = staff_obj

            
            bus_number = request.data.get('bus_number')
            bus.bus_number = bus_number

            bus_type = request.data.get('bus_type')
            bus.bus_type = bus_type

            # Convert features from JSON string to a Python list
            features = request.data.get('features')
            if features:
                bus.features = json.loads(features)  # Convert JSON string to Python list
                

            bus_image = request.FILES.get('bus_image')
            if bus_image:
                bus.bus_image = bus_image

            # Convert total_seats to integer before updating
            total_seats = request.data.get('total_seats')
            if total_seats:
                try:
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
            # Fetch all schedules
            all_buses = Bus.objects.all()
            assigned_bus_ids = Schedule.objects.values_list('bus_id', flat=True).distinct()
            unassigned_buses = all_buses.exclude(id__in=assigned_bus_ids)
            bus_serializer = BusSerializer(unassigned_buses, many=True)
            
            schedules = Schedule.objects.all()
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
            route_id=request.data.get('route')
            route_obj=Route.objects.get(id=route_id)
            
            bus_id=request.data.get('bus')
            bus_obj=Bus.objects.get(id=bus_id)
            departure=request.data.get('departure_time')
            arrival_time=request.data.get('arrival_time')
            price= request.data.get('price')
            
            Schedule.objects.create(bus=bus_obj,route=route_obj,departure_time=departure,arrival_time=arrival_time,price=price)
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
            schedule=Schedule.objects.get(id=id)
            schedule.delete()
            return Response({"success":True,"message":"Schedule deleted Successfully"})            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
        



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


class BookingAPiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        try:
            booking=Booking.objects.all().order_by('-booked_at')
            serializer=BookingSerializer(booking,many=True)
            return Response({'success':True,'data':serializer.data},status=200)
            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
    
    
    def patch(self,request,*args,**kwargs):
        try:
            print(request.data)
            id=kwargs.get('id')
            booking_obj=Booking.objects.get(id=id)
            
            booking_status=request.data.get('status')
            booking_obj.booking_status=booking_status
            booking_obj.save()
            return Response({'success':True,'message':"Booking Status Updated Successfully"})
        except Exception as e:
            return Response({'success':True,'error':str(e)},status=400)
        