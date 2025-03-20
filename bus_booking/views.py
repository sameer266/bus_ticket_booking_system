from django.contrib.auth import authenticate
from django.db.models import Count
from datetime import datetime

from custom_user.models import CustomUser,UserOtp
from route.models import Route,Schedule,Trip,CustomerReview
from bus.models import Bus,BusReservation
from booking.models import Commission,Booking

from custom_user.serializers import CustomUserSerializer
from route.serializers import RouteSerializer,ScheduleSerializer,CustomReviewSerializer,BusScheduleSerializer,BusReservationSerializer



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
            user=authenticate(phone=phone,password=password)
            if user:
                
                print(user.phone)
                refresh = RefreshToken.for_user(user)
                if user:
                    serializer = CustomUserSerializer(user)
        
                    return Response({"success": True, "refresh": str(refresh), "access": str(refresh.access_token), "user": serializer.data}, status=200)
                else:
                    return Response({"success": False, "error": "Invalid Phone number and Password "}, status=400)
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


# ====== Register ======
class Register(APIView):
    
    def post(self, request):
        try:
            full_name = request.data.get('full_name')
            phone = request.data.get('phone')
            email = request.data.get('email')
            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')
            if password == confirm_password:
                user = CustomUser.objects.create_user(full_name=full_name,
                                                      phone=phone,
                                                      password=password,
                                          email=email,
                                                      role='customer')
                serializer = CustomUserSerializer(user)
                if user:
                    return Response({"success": True, "message": "Mormal  User created Successfully", "data": serializer.data})
                else:
                    return Response({"success": False, "error": "Error in creating User"}, status=401)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=401)
        
# ======Forget Password ======
class ForgetPassword(APIView):
    
    def post(self, request):
        try:
            phone = request.data.get("phone")
            user = CustomUser.objects.get(phone=phone, role="customer")
            if user:
                return Response({"success": True, "message": " Email found "}, status=200)
            else:
                return Response({"success": False, "error": "Email not found"}, status=400)
                
        except Exception as e:
            return Response({"success": False, "error": str(e)})



# ==== Otp Send ========
class SendOtp(APIView):
    def post(self,request):
        try:
            phone=request.data.get('phone')  
            if CustomUser.objects.filter(phone=phone).exists():
                return Response({'success':False,"error":"Phone number Already exists "})
            
            otp_number=UserOtp.generate_otp()
            UserOtp.objects.create(otp=otp_number,phone=phone)
            return Response({'success':True,'otp':otp_number,'phone':phone,'message':"Otp is valid for 5 minutes only"},status=200)
      
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)


# ==== Verify OTP ====
class VerifyOtp(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        otp = request.data.get("otp")

        if not phone or not otp:
            return Response({"success": False, "error": "Phone and OTP are required"}, status=400)

        otp_obj = UserOtp.objects.filter(phone=phone, otp=otp).first()
        if not otp_obj:
            return Response({"success": False, "error": "Invalid OTP"}, status=400)
        
        user, created = CustomUser.objects.get_or_create(phone=phone, defaults={"full_name": "None"})

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({"success": True, "message": "OTP verified successfully", "phone": phone, "access": access_token}, status=200)


# ==== Register User (Set Password) ====
class RegisterUserOtp(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
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
            route_objs = Route.objects.filter(source=source, destination=destination)
            
            print("Route",route_objs)
          
            schedule = Schedule.objects.filter(route__in=route_objs)
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

# ========= Popular Routes =============
class PopularRoutes(APIView):
    def get(self,request):
        try:
            top_routes = Route.objects.values('id','source','destination').annotate(route_count=Count('id')).order_by('-route_count')[:4] 
            return Response({'success':True,'data':top_routes},status=200)
        
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)    



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
 

# ========= Bus Reservation =============
class BusReservationList(APIView):
    def get(self, request):
        try:
            buses = Bus.objects.all()
            bus_data = []

            for bus in buses:
                is_available = BusReservation.is_bus_available(bus)
                if is_available:
                    bus_info = BusScheduleSerializer(bus).data
                    bus_data.append(bus_info)
            
            return Response({'success': True, 'data': bus_data}, status=200)
        except Exception as e:
            return Response({'success': False, "error": str(e)}, status=400)

    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def post(self, request, *args, **kwargs):
        try:
            user=request.user
            bus_id = kwargs.get('id')
            bus = Bus.objects.get(id=bus_id)
            BusReservation(bus=bus,user=user)
            return Response({'success':True,'message':'Bus reserved successfully'},status=200)
        

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)
