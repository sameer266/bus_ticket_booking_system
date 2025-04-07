"""
URL configuration for bus_booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from django.shortcuts import redirect

# Admin Site Config
admin.sites.AdminSite.site_header = 'Go Sewa Admin Panel'
admin.sites.AdminSite.site_title = 'Go Sewa'
admin.sites.AdminSite.index_title = 'Admin Panel'

urlpatterns = [
    # ================== Admin Panel ==================
    path('admin/', admin.site.urls),

    # ================== Authentication Views ==================
    path('', lambda request: redirect('login', permanent=False)),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('send-otp/', views.send_otp, name="signup"),
    path('verify-otp/', views.verify_otp, name="verify_otp"),
    path('reset-password/', views.reset_password, name="reset_password"),



    # ================== Admin Dashboard ==================
    path('', include('booking.urls')),
    
  
    

# ==================  APIs ==================
  # ================== Authentication APIs ==================
    path('api/login/', views.LoginView.as_view(), name='token_obtain_login'),
    path('api/logout/', views.LogoutView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/forget_password/', views.ForgetPassword.as_view()),



    # ================== Normal User APIs ==================
    path('api/', include('custom_user.urls')),
    path('api/send_otp/', views.SendOtp.as_view()),
    path('api/verify_otp/', views.VerifyOtp.as_view()),
    path('api/register_user/', views.RegisterUserOtp.as_view()),

    # ================== Web Home Page APIs ==================
    path('api/all_routes/', views.AllRoutesConatinsSchedule.as_view()),
    path('api/all_schedule/', views.AllSchedule.as_view()),

    # ================== Search Routes ==================
    path('api/filter_schedule/', views.FilterRoute.as_view()),

    # ================== Popular Routes ==================
    path('api/popular_routes/', views.PopularRoutes.as_view()),

    # ================== Reviews and Buses ==================
    path('api/all_reviews/', views.AllReveiews().as_view()),
    path('api/all_buses/', views.AllBuses.as_view()),
    path('api/routes_all_buses/<int:id>/', views.RoutesBusList.as_view()),

    # ================== Vehicle Types and Reservations ==================
    path('api/vechicle_types/', views.VechicleTypeList.as_view()),
    path('api/vechicle_list/type/<id>/', views.VechicleReservationList.as_view()),  # List all vehicles of one type
    path('api/vechicle_detail/<int:id>/', views.VehicleOneDetails.as_view()),
    path('api/vechicle_reservation_create/', views.VechicleReeservationBookingApiView.as_view()),

    # ================== Booking APIs ==================
    path('admin_bookinglist/', views.BookingAPiView.as_view()),
    path('api/vechicle_reservation_booking_list/', views.UserVechicleReservationBookingListApiView.as_view()),
    path('api/bus_seat_booking_list/', views.UserSeatBookingListApiView.as_view()),

    # ================== Bus Layout ==================
    path('api/admin_buslayout/<int:id>/', views.BusLayoutApiView.as_view()),
]

# ================== Static Files in Debug Mode ==================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
