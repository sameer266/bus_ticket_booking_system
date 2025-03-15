from django.contrib.auth import authenticate
from django.db.models import Count
from datetime import datetime

from custom_user.models import CustomUser, UserOtp
from route.models import Route, Schedule, Trip, CustomerReview
from bus.models import Bus, TicketCounter
from booking.models import Commission, Booking

from custom_user.serializers import CustomUserSerializer
from route.serializers import (
    RouteSerializer, ScheduleSerializer, CustomReviewSerializer, 
    BusScheduleSerializer, BookingSerializer, TripSerilaizer, TicketCounterSerializer,
    BusSerializer
)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

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
    
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        try:
            bus=Bus.objects.all()
            serilaizer=BusSerializer(bus,many=True)
            return Response({"success":True,"data":serilaizer.data},status=200)
            
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)