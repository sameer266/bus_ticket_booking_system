from django.contrib.auth import authenticate
from custom_user.models import CustomUser

from custom_user.serializers import CustomUserSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response



class LoginView(APIView):
    
    def post(self,request):
        try:
            email=request.data.get('email')
            password=request.data.get('password')
            print(request.data)
            user=authenticate(email=email,password=password)
            print(user)
            refresh=RefreshToken.for_user(user)
            if user:
                serializer=CustomUserSerializer(user)
    
                return Response({"success":True,"refresh":str(refresh),"access":str(refresh.access_token),"user":serializer.data},status=200)
            else:
                return Response({"success":False,"error":"Invalid Username and Password "},status=40)
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)
            
    

class Register(APIView):
    
    def post(self,request):
        try:
            full_name=request.data.get('full_name')
            phone=request.data.get('phone')
            email=request.data.get('email')
            password=request.data.get('password')
            confirm_password=request.data.get('confirm_password')
            if password == confirm_password:
                user=CustomUser.objects.create_user(full_name=full_name,
                                                    phone=phone,
                                                    password=password,
                                                    email=email,
                                                    role='customer')
                serializer=CustomUserSerializer(user)
                if user:
                    return Response({"success":True,"message":"Normal User created Successfully","data":serializer.data})
                else:
                    return Response({"success":False,"error":"Error in creating User"},status=401)
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=401)
        

class ForgetPassword(APIView):
    
    def post(self,request):
        try:
            email=request.data.get(email)
            user=CustomUser.objects.get(email=email,role="customer")
            if user:
                return Response({"success":True,"message":" Email found "},status=200)
            else:
                return Response({"success":False,"error":"Email not found"},status=400)
                
        except Exception as e:
            return Response({"success":False,"error":str(e)})
    