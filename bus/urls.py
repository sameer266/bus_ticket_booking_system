from django.urls import path, include
from . import views
urlpatterns = [
    path('bus-admin/dashboard/',views.bus_admin_dashboard,name="bus_admin_dashboard"),
   

    
]