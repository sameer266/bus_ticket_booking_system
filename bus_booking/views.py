from django.contrib.auth import authenticate
from django.db.models import Count
from django.shortcuts import render,redirect
from django.contrib.auth import login,logout
from custom_user.models import CustomUser
from django.contrib.auth import authenticate
from datetime import datetime
from django.contrib import messages

from custom_user.models import CustomUser,UserOtp
from route.models import Route,Schedule,CustomerReview,Notification
from bus.models import Bus,BusReservation,VechicleType,SeatLayoutBooking
from booking.models import Booking,BusReservationBooking
from django.shortcuts import get_object_or_404
from custom_user.serializers import CustomUserSerializer
from route.serializers import RouteSerializer,ScheduleSerializer,CustomReviewSerializer,BusScheduleSerializer,BusReservationSerializer,VechicleTypeSerializer,VechicleUserReservationBookingSerializer,UserBookingSerilaizer,BookingSerializer,SeatLayoutBookingSerializer,NotificationSerializer




from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response



       


# =======  Login ========

def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        if password == "counter@123":
            message = "Please Reset Password"
            return render(request, 'pages/reset_new_password.html', {"message": message,"phone":phone})
        user = authenticate(phone=phone, password=password)
        print(user)
        
            
        if user:
            if user.role=="admin" or user.role=="sub_admin":
                login(request,user)
                print(user)
                return redirect('admin_dashboard')
            else:
                error_message = "Invalid User"
            return render(request, 'pages/login.html', {'error_message': error_message})
                
        else:
            error_message = "Invalid phone number or password"
            return render(request, 'pages/login.html', {'message': error_message})
    return render(request, 'pages/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')




def send_otp(request):
    if request.method == 'POST':
        try:
            
            print(request.POST)
            phone = request.POST.get('phone')
            full_name = request.POST.get('full_name')

            # Check if the phone number already exists
            if CustomUser.objects.filter(phone=phone).exists():
                return render(request, 'send_otp.html', {'error': 'Phone number already exists'})

            otp_number = UserOtp.generate_otp()
            # Store the OTP in the database with a reference to the phone number
            UserOtp.objects.create(otp=otp_number, phone=phone, temp_name=full_name)

            # Redirect to OTP verification page with success message
            return render(request, 'pages/verify_otp.html', {'phone': phone, 'message': 'OTP has been sent. Please verify!'})

        except Exception as e:
            return render(request, 'pages/send_otp.html', {'error': str(e)})
    return render(request, 'pages/send_otp.html')


def verify_otp(request):
    if request.method == 'POST':
       
        otp = request.POST.get('otp')
        try:
            user_otp = UserOtp.objects.get(otp=otp)
            user = user_otp.user
            user_otp.delete()
            login(request, user)
            return redirect('admin_dashboard')
        except UserOtp.DoesNotExist:
            return render(request, 'pages/verify_otp.html', {'message': 'Invalid OTP'})
    return render(request, 'pages/verify_otp.html')
        

def unauthenticated_reset_password(request):
    message = ""
    if request.method == "POST":
            if request.POST.get("phone"):
                p1 = request.POST.get("password")
                p2 = request.POST.get("confirm_password")
                if p1 == p2:
                    print(request.POST)
                    phone=request.POST.get('phone')
                    print(phone)
                    user=CustomUser.objects.get(phone=phone)
                    user.set_password(p1)
                    user.save()
                
                    message= "Password reset successfully."
                    return render(request, 'pages/login.html', {'message': message})
                else:
                    message = "Passwords do not match."
                    return render(request, 'pages/reset_new_password.html', {'message': message})
    return render(request, 'pages/login.html', {'message': message})


def reset_password(request):
    message = ""
    try:
     
        if request.method == "POST":
            if request.POST.get("phone"):
                p1 = request.POST.get("password")
                p2 = request.POST.get("confirm_password")
                if p1 == p2:
                   
                    phone=request.POST.get('phone')
                    print(phone)
                    user=CustomUser.objects.get(phone=phone)
                    user.set_password(p1)
                    user.save()
                    login(request,user)
                    messages.success(request, "Password reset successfully.")
                    return render(request, 'pages/login.html', {'message': message})
                else:
                    message = "Passwords do not match."
                    return render(request, 'admin/reset_password.html', {'message': message})
                
            user = request.user
            print(request.POST)
            p1 = request.POST.get("password")
            p2 = request.POST.get("confirm_password")
           
            if p1 == p2:
                print("YR")
                user.set_password(p1)
                user.save()
                print("Yes ")
                messages.success(request, "Password reset successfully.")
                return redirect('admin_dashboard')
            else:
                message = "Passwords do not match."
                return render(request, 'admin/reset_password.html', {'message': message})
    except CustomUser.DoesNotExist:
        message = "Invalid reset link."
    
    return render(request, 'admin/reset_password.html', {'message': message})



def forget_password(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        try:
           
                if CustomUser.objects.filter(phone=phone).exists():
                    user = CustomUser.objects.get(phone=phone, role="customer")
                    otp_number = UserOtp.generate_otp()
                    # Send the OTP via SMS
                    sms_response = UserOtp.send_sms(phone, otp_number)

                    if "error" in sms_response or sms_response.get("response_code") != 200:
                        return render(request, 'pages/forget_password.html', {'error': 'Failed to send SMS'})

                    # Save or update the OTP
                    user_otp, _ = UserOtp.objects.get_or_create(
                        user=user,
                        phone=phone,
                        temp_name= user.full_name
                    )

                    user_otp.otp = otp_number
                    user_otp.save()

                    return render(request, 'pages/verify_otp.html', {'phone': phone, 'message': 'OTP has been sent. Please verify!'})
                else:
                    return render(request, 'pages/forget_password.html', {'message': 'User not found'})

        except CustomUser.DoesNotExist:
            return render(request, 'pages/forget_password.html', {'message': 'User not found'})
    return render(request, 'pages/forget_password.html')



# ======== Api ============
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
            print(" Incoming data:", request.data)
            phone = request.data.get("phone")

            if not phone:
                return Response({"success": False, "error": "Phone number is required"}, status=400)

            try:
                user = CustomUser.objects.get(phone=phone, role="customer")
            except CustomUser.DoesNotExist:
                return Response({"success": False, "error": "User not found"}, status=404)

            otp_number = UserOtp.generate_otp()
            print(f" Found user: {user.full_name} | Phone: {user.phone} | OTP: {otp_number}")

            # Send the OTP via SMS
            sms_response = UserOtp.send_sms(phone, otp_number)

            if "error" in sms_response or sms_response.get("response_code") != 200:
                return Response({'success': False, 'error': 'Failed to send SMS'}, status=400)

            # Save or update the OTP
            user_otp, _ = UserOtp.objects.get_or_create(
                user=user,
                phone=phone,
                defaults={"temp_name": user.full_name}
            )

            user_otp.otp = otp_number
            user_otp.save()

            return Response({
                "success": True,
                "message": "OTP sent successfully",
                "otp": otp_number,
                "phone": user.phone
            }, status=200)

        except Exception as e:
            print(f" Exception in ForgetPassword: {e}")
            return Response({"success": False, "error": str(e)}, status=500)


# ========= Reset password ======
class ResetPassword(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            print(request.data)
            password = request.data.get('password')
            if not password:
                return Response({"success": False, "error": "Password is required."}, status=400)
            
            user = request.user
            user.set_password(password)
            user.save()

            # Delete OTP if exists
            otp_user = UserOtp.objects.filter(user=user).first()
            if otp_user:
                otp_user.delete()

            return Response({"success": True, "message": "Password reset successfully."}, status=200)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


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
            try:
                UserOtp.send_sms(phone,otp_number)
            except Exception as e:
                return Response({'success':False,'error':str(e)},status=400)
     
            user,created=UserOtp.objects.get_or_create(phone=phone,temp_name=full_name)
            if user:
                user.otp=otp_number
                user.save()
                
            return Response({'success':True,'otp':otp_number,'phone':phone,'message':"Otp is valid for 5 minutes only"},status=200)
      
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)


# ==== Verify OTP ====
class VerifyOtp(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp')
            if not otp:
                return Response({"success": False, "error": "OTP is required"}, status=400)

            otp_obj = UserOtp.objects.filter(otp=otp).first()
            if not otp_obj:
                return Response({"success": False, "error": "Invalid OTP"}, status=400)

            user, created = CustomUser.objects.get_or_create(
                phone=otp_obj.phone,
                full_name= otp_obj.temp_name, 
                role="customer"
            )
            otp_obj.user = user
            otp_obj.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                "success": True,
                "message": "OTP verified successfully",
                "phone": otp_obj.phone,
                "full_name": otp_obj.temp_name,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=200)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


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
        Schedule.update_all_status()
        schedule=Schedule.objects.all()
        serializer=ScheduleSerializer(schedule,many=True)
        return Response({"success":True,"data":serializer.data},status=200)



# ========= Filter Route ==========
class FilterSchedule(APIView):
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
    def get(self,*args,**kwargs):
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

class VehicleListSource(APIView):
    def get(self,request):
        try:
            source = request.query_params.get('source')
            print(source)
            if source:
                vechicles = BusReservation.objects.filter(source=source)
                data_list=[]
                for vechicle in vechicles:
                    data={
                        "id":vechicle.id,
                        "name":vechicle.name,
                        "type":vechicle.type.name,
                        "vechicle_number":vechicle.vechicle_number,
                        "vechicle_model":vechicle.vechicle_model,
                        "image":vechicle.image.url,
                        "color":vechicle.color,
                        "driver":vechicle.driver.full_name,
                        "staff":vechicle.staff.full_name,
                        "total_seats":vechicle.total_seats,
                        "price":vechicle.price,
                        "source":vechicle.source,
                    }
                    data_list.append(data)
                
                return Response({'success':True,'data':data_list}, status=200)
            
          
            
        except Exception as e:
            return Response({'success':False,'error':str(e)}, status=400)
        
        
class VechicleTypeList(APIView):
    def get(self,request):
        try:
            vechicle=VechicleType.objects.all()
            serializer=VechicleTypeSerializer(vechicle,many=True)
            return Response({"success":True,"data":serializer.data},status=200)
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)

class VehicleOneDetails(APIView):
    def get(self, request, *args, **kwargs):
        try:
            id = kwargs.get('id')
            bus_reservation = get_object_or_404(BusReservation, id=id)
            data = {
                'id':bus_reservation.id,
                'name': bus_reservation.name,
                'type': bus_reservation.type.name,
                'image': bus_reservation.image.url,
                'vehicle_number': bus_reservation.vechicle_number,
                'vehicle_model': bus_reservation.vechicle_model,
                'color': bus_reservation.color,
                'driver': getattr(bus_reservation.driver, 'full_name', None),
                'staff': getattr(bus_reservation.staff, 'full_name', None),
                'total_seats': bus_reservation.total_seats,
                'price': bus_reservation.price,
            }

            return Response({'success': True, 'data': data}, status=200)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)
        
   # ========= Bus Reservation =============
class VechicleReservationList(APIView):
    def get(self, request, *args, **kwargs):
        try:
            id = kwargs.get('id')

            if id in ["null", " ", None]:
                bus_reservations = BusReservation.objects.all()
                serializer = BusReservationSerializer(bus_reservations, many=True)
                return Response({"success": True, "data": serializer.data}, status=200)

            bus_reservations = BusReservation.objects.filter(type__id=id)

            if not bus_reservations.exists():
                return Response({"success": False, "error": "No bus reservations found"}, status=404)


            data_list = []
            for bus_reservation in bus_reservations:
                data = {
                    "id":bus_reservation.id,
                    "name": bus_reservation.name,
                    "type": bus_reservation.type.name,
                    "vechicle_number": bus_reservation.vechicle_number,
                    "vechicle_model": bus_reservation.vechicle_model,
                    "image": bus_reservation.image.url if bus_reservation.image else None,
                    "color": bus_reservation.color,
                    "driver": bus_reservation.driver.full_name if bus_reservation.driver else None,
                    "staff": bus_reservation.staff.full_name if bus_reservation.staff else None,
                    "total_seats": bus_reservation.total_seats,
                    "price": bus_reservation.price,
                    "source":bus_reservation.source
                }
                data_list.append(data)

            return Response({"success": True, "data": data_list}, status=200)

        except Exception as e:
            return Response({'success': False, "error": str(e)}, status=400)



# ======= Bus Reservation Booking ===========
class  VechicleReeservationBookingApiView(APIView):
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
            print(start_date)
        
        
            BusReservationBooking.objects.create(user=user,bus_reserve=busReserve_obj,source=source,destination=destination,date=date,start_date=start_date)
            
            return Response({'success':True,'message':'Bus reserved successfully'},status=200)
        
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)


# ======= Vechicle Reservation or Booking one user List  ==========

class UserVechicleReservationBookingListApiView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
                user = request.user
                reserve=BusReservationBooking.objects.filter(user=user).order_by('-created_at')
                serilaizer_reserve=VechicleUserReservationBookingSerializer(reserve,many=True)
            
                return Response({"success": True, "data":serilaizer_reserve.data}, status=200)


# ======== Seat Booking list of one user ================
class UserSeatBookingListApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    def get(self, request):
        try:
                user = request.user
                user=CustomUser.objects.get()
                bookings_seat = Booking.objects.filter(user=user).order_by('-booked_at')
                serializer_seat = UserBookingSerilaizer(bookings_seat, many=True)
                return Response({'success':True,'data':serializer_seat.data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        

# ========== Booking Management  =================
class SeatBookingAPiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        try:
            booking=Booking.objects.filter(user=request.user).order_by('-booked_at')
            serializer=BookingSerializer(booking,many=True)
            return Response({'success':True,'data':serializer.data},status=200)
            
        except Exception as e:
            return Response({'success':False,"error":str(e)},status=400)
    

# ========= Bus Layout =========
class BusLayoutApiView(APIView):
   
    def get(self, request, *args, **kwargs):
        try:
            schedule_id = kwargs.get('id')
            if not schedule_id:
                return Response({"success": False, "error": "Bus ID not provided"}, status=400)
            schedule=Schedule.objects.get(id=schedule_id)
            serializer=ScheduleSerializer(schedule)
            bus_layout = SeatLayoutBooking.objects.get(schedule=schedule)
            layout_searilaizer=SeatLayoutBookingSerializer(bus_layout)
            
            return Response({"success": True,"bus_schedule": serializer.data, 'layout':layout_searilaizer.data}, status=200)
        
        except SeatLayoutBooking.DoesNotExist:
            return Response({"success": False, "error": "Bus layout not found"}, status=404)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)
        
    # =========== Notification ==========
    
class UserNotificationApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        user=request.user
        notification=Notification.objects.filter(user=user).order_by('-created_at')
        serializer=NotificationSerializer(notification,many=True)
        return Response({'success':True,'data':serializer.data},status=200)
    
    def post(self,request,id):
        is_read=request.data.get('is_read')
        notification=Notification.objects.get(id=id)
        notification.is_read=is_read
        notification.save()
        return Response({'success':True,'message':'Nofication read success'},status=200)
    
    
    