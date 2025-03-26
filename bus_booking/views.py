from django.contrib.auth import authenticate
from django.db.models import Count
from datetime import datetime

from custom_user.models import CustomUser,UserOtp,System
from route.models import Route,Schedule,Trip,CustomerReview
from bus.models import Bus,BusReservation,BusLayout,Driver,Staff,VechicleType
from booking.models import Commission,Booking,BusReservationBooking

from custom_user.serializers import CustomUserSerializer,SystemSerializer
from route.serializers import RouteSerializer,ScheduleSerializer,CustomReviewSerializer,BusScheduleSerializer,BusLayoutSerilizer,BusReservationSerializer,VechicleTypeSerializer,BusReservationBookingSerializer




from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes

       



# ======Login ======
class LoginView(APIView):
    def post(self, request):
        try:
            phone = request.data.get('phone')
            password = request.data.get('password')
            print(request.data)

            user = authenticate(phone=phone, password=password)

            if user:
                print(user.phone)
                refresh = RefreshToken.for_user(user)
                serializer = CustomUserSerializer(user)
                
                return Response({
                    "success": True,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": serializer.data
                }, status=200)

            return Response({"success": False, "error": "Invalid phone number or password"}, status=400)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


     
import logging

logger = logging.getLogger(__name__)

class LogoutView(APIView):
    def post(self, request):
        try:
            print(request.data)
           
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                return Response({"success": False, "error": "Refresh token is required"}, status=400)
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User {request.user} logged out successfully.")

            return Response({"success": True, "message": "Logout successful"}, status=200)

        
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({"success": False, "error": str(e)}, status=400)


# # ====== Register ======
# class Register(APIView):
    
#     def post(self, request):
#         try:
#             full_name = request.data.get('full_name')
#             phone = request.data.get('phone')
#             email = request.data.get('email')
#             password = request.data.get('password')
#             confirm_password = request.data.get('confirm_password')
#             if password == confirm_password:
#                 user = CustomUser.objects.create_user(full_name=full_name,
#                                                       phone=phone,
#                                                       password=password,
#                                           email=email,
#                                                       role='customer')
#                 serializer = CustomUserSerializer(user)
#                 if user:
#                     return Response({"success": True, "message": "Mormal  User created Successfully", "data": serializer.data})
#                 else:
#                     return Response({"success": False, "error": "Error in creating User"}, status=401)
#         except Exception as e:
#             return Response({"success": False, "error": str(e)}, status=401)
        
# ======Forget Password ======
class ForgetPassword(APIView):
    
    def post(self, request):
        try:
            phone = request.data.get("phone")
            user = CustomUser.objects.get(phone=phone, role="customer")
            if user:
                return Response({"success": True, "message": " User found "}, status=200)
            else:
                return Response({"success": False, "error": "User not found"}, status=400)
                
        except Exception as e:
            return Response({"success": False, "error": str(e)})


# ========= Register user ==========
# ==== Otp Send ========
class SendOtp(APIView):
    def post(self,request):
        print(request.data)
        try:
            phone=request.data.get('phone')  
            full_name=request.data.get('full_name')
            
            if CustomUser.objects.filter(phone=phone).exists():
                return Response({'success':False,"error":"Phone number Already exists "},status=400)
            
            otp_number=UserOtp.generate_otp()
            UserOtp.objects.create(otp=otp_number,phone=phone,temp_name=full_name)
            return Response({'success':True,'otp':otp_number,'phone':phone,'message':"Otp is valid for 5 minutes only"},status=200)
      
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)


# ==== Verify OTP ====
class VerifyOtp(APIView):
    def post(self, request):
        print(request.data)
        otp = request.data.get('otp')
     
        if not otp:
            return Response({"success": False, "error": " OTP are required"}, status=400)

        otp_obj = UserOtp.objects.filter(otp=otp).first()
        print("Full_name",otp_obj)
        if not otp_obj:
            return Response({"success": False, "error": "Invalid OTP"}, status=400)
        
        user, created = CustomUser.objects.get_or_create(phone=otp_obj.phone, full_name=otp_obj.temp_name,role='customer')
        otp_obj.user=user
        otp_obj.save()
        
        if created:
            print(user)
            
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({"success": True, "message": "OTP verified successfully", "phone": otp_obj.phone,"full_name":otp_obj.temp_name, "access": access_token,"refresh":str(refresh)},status=200)


# ==== Register User (Set Password) ====
class RegisterUserOtp(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        user = request.user
        password = request.data.get('password')

        if not password:
            return Response({"success": False, "error": "Password is required"}, status=400)

        user.set_password(password)
        user.save()

        return Response({"success": True, "message": "Password created successfully"}, status=200)        
        


# ===== All Routes  that is availabel in schedule =========
class AllRoutesConatinsSchedule(APIView):
    def get(self, request):
        # Get all routes
        routes = Route.objects.all()
        route_data = []

        for route in routes:
            # Check if the route is available in the Schedule model
            is_available = Schedule.objects.filter(route=route).exists()

            # Add the route data with the availability status
            route_info = RouteSerializer(route).data
            route_info['isAvailable'] = is_available  # Add 'isAvailable' field

            route_data.append(route_info)

        return Response({"success": True, "data": route_data}, status=200)
    
    

# ====== All Schedule ==========      
class AllSchedule(APIView):
    def get(self,request):
        schedule=Schedule.objects.all()
        serializer=ScheduleSerializer(schedule,many=True)
        return Response({"success":True,"data":serializer.data},status=200)



# ========= Filter Route ==========
class FilterRoute(APIView):
    def get(self, request):
        try:
            # Get the query parameters
            print("Search", request.query_params)
            source = request.query_params.get('source')
            destination = request.query_params.get('destination')
            departure_time = request.query_params.get('departure_time')  # Expecting a date string in format YYYY-MM-DD

            # Check for missing parameters
            if not source or not destination or not departure_time:
                return Response({"success": False, "error": "Missing required parameters"}, status=400)

            try:
              
                departure_date = datetime.strptime(departure_time, "%Y-%m-%d").date()
            except ValueError:
                return Response({"success": False, "error": "Invalid date format, expected YYYY-MM-DD"}, status=400)
            route_objs = Route.objects.filter(
                source__icontains=source, 
                destination__icontains=destination
            )
            
            print("Route",route_objs)
          
            schedule = Schedule.objects.filter(
                route__in=route_objs,
                departure_time__date=departure_date
            )
            print("Schedule",schedule)

            if not schedule.exists():
                return Response({"success": True, "data": [],"source": source,
                "destination": destination,
                "departure_date": departure_date}, status=200)

        
            serializer = ScheduleSerializer(schedule, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "source": source,
                "destination": destination,
                "departure_date": departure_date  
            }, status=200)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

from django.conf import settings

# ========= Popular Routes =============
class PopularRoutes(APIView):
    def get(self, request):
        try:
            # Fetching the popular routes
            top_routes = Route.objects.values('id', 'source', 'destination', 'image') \
                .annotate(route_count=Count('id')) \
                .order_by('-route_count')[:4]

            # Adding the full image path to the 'image' field
            for route in top_routes:
                # Construct the full image URL if the image field is not empty
                route['image'] = settings.MEDIA_URL + route['image'] if route['image'] else None

            # Return the response with the top routes data
            return Response({'success': True, 'data': top_routes}, status=200)

        except Exception as e:
            # Return error response if an exception occurs
            return Response({"success": False, "error": str(e)}, status=400)


# ====== All Reviews =============
class AllReveiews(APIView):
    def get(self,request):
        try:
            reviews=CustomerReview.objects.all().order_by('-created_at')[ :4]
            serializer=CustomReviewSerializer(reviews,many=True)
            return Response({"success":True,"data":serializer.data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        

# ===== All Buses with routes =======
class AllBuses(APIView):
    def get(self,request):
        try:
            bus=Bus.objects.all().order_by('-available_seats')
            serializer=BusScheduleSerializer(bus,many=True)
            return Response({"success":True,"data":serializer.data},status=200)
        except Exception as e:
            return Response({"error":True,"error":str(e)},status=400)

# ====== show all  buses of one route ==========
class RoutesBusList(APIView):
    def get(self,request,*args,**kwargs):
        try:
            route_id=kwargs.get('id')
            route_obj=Route.objects.get(id=route_id)
            schedule=Schedule.objects.filter(route=route_obj)
            serializer=ScheduleSerializer(schedule,many=True)
            return Response({"success":True,"data":serializer.data},status=200)
        except Exception as e:
            return Response({"success":False,'error':str(e)},status=200)
 

# =====================
# Vechicle Type 
# =====================
class VechicleTypeList(APIView):
    def get(self,request):
        try:
            vechicle=VechicleType.objects.all()
            serializer=VechicleTypeSerializer(vechicle,many=True)
            return Response({"success":True,"data":serializer.data},status=200)
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)
    
    
# ========= Bus Reservation =============
class BusReservationList(APIView):
    def get(self, request, *args, **kwargs):
        try:
            id=kwargs.get('id')
            if id == "null" or id ==" ":
                bus_reservation = BusReservation.objects.all()
                serializer = BusReservationSerializer(bus_reservation, many=True)
                return Response({"success": True, "data": serializer.data}, status=200)
            bus_reservation = BusReservation.objects.filter(type__id=id)
            serializer = BusReservationSerializer(bus_reservation, many=True)
            return Response({"success": True, "data": serializer.data}, status=200)
        except Exception as e:
            return Response({'success': False, "error": str(e)}, status=400)
        

    
# ======= Bus Reservation Booking ===========
class  BusReeservationBookingApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def post(self, request):
        try:
            print(request.data)
            user=request.user
            print(user.phone)
            
            id=request.data.get('vehicle_id')
            busReserve_obj=BusReservation.objects.get(id=id)
            source=request.data.get('source')
            destination=request.data.get('destination')
            date=request.data.get('days')
            start_date_str=request.data.get('date')
            start_date = datetime.strptime(start_date_str, "%Y/%m/%d").date()
            
            BusReservationBooking.objects.create(user=user,bus_reserve=busReserve_obj,source=source,destination=destination,date=date,start_date=start_date)
            return Response({'success':True,'message':'Bus reserved successfully'},status=200)
        
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

# ========= Bus Layout =========
class BusLayoutApiView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            bus_id = kwargs.get('id')
            if not bus_id:
                return Response({"success": False, "error": "Bus ID not provided"}, status=400)
            
            bus_layout = BusLayout.objects.get(bus_id=bus_id)
            layout_searilaizer=BusLayoutSerilizer(bus_layout)
            
            schedule=Schedule.objects.get(bus__id=bus_id)
            serializer=ScheduleSerializer(schedule)
            return Response({"success": True, "bus_schedule": serializer.data,'layout':layout_searilaizer.data}, status=200)
        
        except BusLayout.DoesNotExist:
            return Response({"success": False, "error": "Bus layout not found"}, status=404)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
    

class NavAndContactDataApiView(APIView):
    def get(self,request):
        settings=System.objects.all().first()
        serializer=SystemSerializer(settings)
        return Response({'success':True,'data':serializer.data},status=200)