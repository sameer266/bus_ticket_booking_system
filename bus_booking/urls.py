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
from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Admin Site Config
admin.sites.AdminSite.site_header = 'Go Sewa Admin Panel'
admin.sites.AdminSite.site_title = 'Go Sewa'
admin.sites.AdminSite.index_title = 'Admin Panel'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', views.LoginView.as_view(), name='token_obtain_login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
       
    path('api/register/',views.Register.as_view()),
    path('api/forget_password/',views.ForgetPassword.as_view()),
    
    
    # path('api/bus',include('bus.urls')),
    # path('api/booking',include('booking.urls')),
    path('api/',include('route.urls')),
    
]
