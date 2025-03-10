from django.contrib.auth import authenticate
from custom_user.models import CustomUser,UserOtp

from custom_user.serializers import CustomUserSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response

# ======Login ======
class LoginView(APIView):
    
    def post(self, request):
        try:
            phone = request.data.get('phone')
            password = request.data.get('password')
            print(request.data)
            user = authenticate(phone=phone, password=password)
            print(user)
            refresh = RefreshToken.for_user(user)
            if user:
                serializer = CustomUserSerializer(user)
    
                return Response({"success": True, "refresh": str(refresh), "access": str(refresh.access_token), "user": serializer.data}, status=200)
            else:
                return Response({"success": False, "error": "Invalid Phonenumber and Password "}, status=40)
        except Exception as e:
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
                    return Response({"success": True, "message": "Normal User created Successfully", "data": serializer.data})
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
class SendOtp_VerifyOtp(APIView):
    def get(self,request):
        try:
            phone=request.data.get('phone')
            user=CustomUser.objects.get(phone=phone)
            if user:
                otp_number=UserOtp.generate_otp()
                UserOtp.objects.create(user=user,otp=otp_number)
                return Response({'success':True,'otp':otp_number,'phone':user.phone,'message':"Otp is valid for 5 minutes only"},status=200)
                
        except user.DoesNotExist:
            return Response({'success':False,'error':"No User with phone number found"},status=400)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)

    def post(self,request):
        try:
            otp_number=request.data.get('otp')
            otp_obj=UserOtp.objects.get(otp=otp_number)
            if otp_obj:
                if otp_obj.is_expired():
                    return Response({"success":False,'error':"Otp is expired "},status=400)

            return Response({"success":True,"message":"Otp verified successfully"},status=200)
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=401)
        
        