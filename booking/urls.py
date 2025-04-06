from django.contrib import admin
from django.urls import path,include

from . import views
urlpatterns = [
    
     # ======== Admin Dashboard ==========
     path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # ====== Admin Profile ======
    
    path('admin-profile/',views.admin_profile,name="admin_profile"), 
    
    # ===== Admin Ticket Counter =========
    path("admin-ticket-counter/", views.ticket_counter_list, name="ticket_counter_list"),
    path("admin-ticket-counter/edit/<int:id>/", views.edit_ticket_counter, name="edit_ticket_counter"),
    path("admin-ticket-counter/delete/<int:id>/",views.delete_ticket_counter, name="delete_ticket_counter"),
    
    
    
    # ======= user Management ==========
    path('users-management/', views.manage_users, name='manage_users'),
    path('users-delete/<int:id>/', views.delete_user, name='delete_user'),
    
    # ======== Driver and Staff ==========
    path('driver-staff/', views.manage_driver_and_staff, name='manage_driver_and_staff'),
    path('edit-driver/<int:driver_id>/',views.edit_driver, name='edit_driver'),
    path('delete-driver/<int:driver_id>/', views.delete_driver, name='delete_driver'),
    path('edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
   

    path('reservations/', views.vehicle_reservation, name='vehicle-reservation'),
    path('reservations/<int:id>/', views.vehicle_reservation, name='vehicle-reservation'),

   # ======== route ========
    path('routes-management/', views.route_list_and_add, name='route_list_add'),
    path('routes-edit/<int:id>/', views.edit_route, name='edit_route'),
    path('routes-delete/<int:id>/', views.delete_route, name='delete_route'),
    
    # =====  Route to all Bus List =============
    path('route_buslist/<int:id>/',views.route_bus_list,name="route_bus_list"),
    path('route_bus_details/<int:id>/',views.BusDetails.as_view(),name="route_bus_details"),
    
    
  # ======= Bus Management ==========
    path('buses-management', views.bus_list, name='bus_list'),
    path('add-bus/', views.create_bus, name='create_bus'),
    path('edit-bus/<int:bus_id>/edit/', views.edit_bus, name='edit_bus'),
    path('delete-bus/<int:bus_id>/delete/', views.delete_bus, name='delete_bus'),
    
    
    # ======  Schedule ======
    path('schedules-management/', views.schedule_list, name='schedule_list'),
    path('schedules/edit/<int:id>/', views.schedule_edit, name='schedule_edit'),
    path('schedules/delete/<int:id>/', views.schedule_delete, name='schedule_delete'),
    
    # ==== Bus details from schedule =========
    path('bus-list/<int:id>/', views.schedule_bus_details, name='bus_details'),
    path('booking-details/<int:id>/', views.booking_details, name='booking_details'),

    
    # ====== Booking ========
    path('booking-management/', views.booking_management, name='booking_list'),
    
    # ====== Report ========
     path('reports/', views.report_analysis_view, name='report_analysis'),
   
   # ====== System Settings ========
   path('settings/', views.system_settings_view, name='system_settings'),

#  ======== Payment ========
path('payment-details/', views.payment_details, name='payments_details'),
path('update-rate/', views.update_rate, name='update_rate'),
    
    # =========Vechicle Type =========
    path('admin_vehicletype/', views.VehicleTypeViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('admin_vehicletype/<int:pk>/', views.VehicleTypeViewSet.as_view({ 'patch': 'update', 'delete': 'destroy'})),
 
    
    
 
    
   
]