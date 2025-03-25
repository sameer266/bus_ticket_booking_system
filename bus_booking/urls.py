"""
URL configuration for bus_booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""




from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Admin Site Config
admin.sites.AdminSite.site_header = 'Go Sewa Admin Panel'
admin.sites.AdminSite.site_title = 'Go Sewa'
admin.sites.AdminSite.index_title = 'Admin Panel'


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ====== Authentication api =========
    path('api/login/', views.LoginView.as_view(), name='token_obtain_login'),
    path('api/logout/',views.LogoutView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('api/forget_password/',views.ForgetPassword.as_view()),
    
    
    path('api/send_otp/',views.SendOtp.as_view()),
    path('api/verify_otp/',views.VerifyOtp.as_view()),
    path('api/register_user/',views.RegisterUserOtp.as_view()),
    
    # ======== Web Home page Api  ==========
    path('api/all_routes/',views.AllRoutesConatinsSchedule.as_view()),
    path('api/all_schedule/',views.AllSchedule.as_view()),
    
    # ====== Search routes ==============
    path('api/filter_schedule/',views.FilterRoute.as_view()),
    
    # ====== Popular routes =========
    path('api/popular_routes/',views.PopularRoutes.as_view()),
    
    path('api/all_reviews/',views.AllReveiews().as_view()),
    path('api/all_buses/',views.AllBuses.as_view()),
    path('api/routes_all_buses/<int:id>/',views.RoutesBusList.as_view()),
    
    #======== Vechicle Type and Reservation  ============
    path('api/all_vechicle_type/',views.VechicleTypeList.as_view()),
    path('api/vechicle_reservation/<id>/',views.BusReservationList.as_view()),
    path('api/vechicle_reservation_create/',views.BusReeservationBookingApiView.as_view()),
    
    
     # ==== Bus Layout ==========
    path('api/admin_buslayout/<int:id>/',views.BusLayoutApiView.as_view()),
    
    
    # ===== Admin Dashboard ==========
    path('api/',include('booking.urls')),
    
    # ========= Normal User ============
    path('api/',include('custom_user.urls')),

  
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)