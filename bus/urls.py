from django.urls import path, include
from . import views
urlpatterns = [
    path('dashboard/',views.bus_admin_dashboard,name="bus_admin_dashboard"),
    
    path('profile/', views.bus_admin_profile, name='bus_admin_profile'),
    # Placeholder for edit profile (you'll need to create this view)
    # path('profile/edit/', views.edit_bus_admin_profile, name='edit_bus_admin_profile'),
    
    path('schedule-list/',views.schedule_list,name="bus_admin_schedule"),
    path('booking/',views.booking_management,name="bus_admin_booking"),
    path('bus-earnings/',views.bus_payment_details,name="bus_admin_earnings"),
    path('payments/',views.payment_list,name="bus_admin_payments")

    
   

    
]