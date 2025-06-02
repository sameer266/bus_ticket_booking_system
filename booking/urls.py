from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
  # ======== Admin Dashboard ==========
  path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

  # ======== Admin Profile ==========
  path('admin-profile/', views.admin_profile, name="admin_profile"),

  # ======== Admin Ticket Counter Management ==========
  path("admin-ticket-counter/", views.transportation_company_list, name="transportation_company_list"),
  path("admin-ticket-counter/edit/<int:id>/", views.edit_transportation_company, name="edit_transportation_company"),
  path("admin-ticket-counter/delete/<int:id>/", views.delete_transportation_company, name="delete_transportation_company"),

  # ======== Sub Admin Bus List ==========
  path('subadmin-buslist/<int:id>/', views.sub_admin_bus_list, name='subadmin_bus_list'),

  # ======== User Management ==========
  path('users-management/', views.manage_users, name='manage_users'),
  path('users-delete/<int:id>/', views.delete_user, name='delete_user'),

  # ======== Driver and Staff Management ==========
  path('driver-staff/', views.manage_driver_and_staff, name='manage_driver_and_staff'),
  path('edit-driver/<int:driver_id>/', views.edit_driver, name='edit_driver'),
  path('delete-driver/<int:driver_id>/', views.delete_driver, name='delete_driver'),
  path('edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
  path('delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),

  # ======== Vehicle Management ==========
  path('vehicle/', views.vehicle_list, name='vehicle_reservation'),
  path('vehicle/edit/<int:id>/', views.edit_vehicle, name='vehicle_reservation_edit'),
  path('vehicle/delete/<int:id>/',views.delete_vehicle,name="delete_vehicle_reservation"),

  # ======== Vehicle Type Management ==========
  path('vehicle-type-management/', views.vechicle_type_list, name='vehicle_type_list'),
  path('vehicle-type-add/', views.vechicle_type_list, name='create_vehicle_type'),
  path('vehicle-type-edit/<int:id>/', views.edit_vechicle_type, name='edit_vehicle_type'),
  path('vehicle-type-delete/<int:id>/', views.delete_vechicle_type, name='delete_vehicle_type'),
  path('vehicle-type/vehicles/<int:id>', views.vehicleType_vehicle_list, name='vehicle_type_vehicles'),


  # ======== Route Management ==========
  path('routes-management/', views.route_list_and_add, name='route_list_add'),
  path('routes-edit/<int:id>/', views.edit_route, name='edit_route'),
  path('routes-delete/<int:id>/', views.delete_route, name='delete_route'),

  # ======== Route to Bus List ==========
  path('route-buslist/<int:id>/', views.route_bus_list, name="route_bus_list"),
  path('route_bus_details/<int:id>/', views.BusDetails.as_view(), name="route_bus_details"),


# ========== Bus Features ==========
  path('bus-features/',views.bus_featurelist,name='busfeature_lists'),
  path('add-bus-features/',views.add_bus_feature,name="add_bus_feature"),
  path('edit-bus-features/<int:feature_id>/',views.edit_bus_feature,name='edit_busfeature'),
  path('delete-bus-feature/<int:feature_id>/',views.delete_bus_feature,name="delete_bus_feature"),
  
  
  # ======== Bus Management ==========
  path('buses-management/', views.bus_list, name='bus_list'),
  path('add-bus/', views.create_bus, name='create_bus'),
  path('edit-bus/<int:bus_id>/', views.edit_bus, name='edit_bus'),
  path('delete-bus/<int:bus_id>/', views.delete_bus, name='delete_bus'),
  path('get_bus/<int:bus_id>/', views.get_bus, name='get_bus'),

  # ======== Schedule Management ==========
  path('schedules-management/', views.schedule_list, name='schedule_list'),
  path('schedules/edit/<int:id>/', views.schedule_edit, name='schedule_edit'),
  path('schedules/delete/<int:id>/', views.schedule_delete, name='schedule_delete'),

  # ======== Bus Details from Schedule ==========
  path('bus-list/<int:id>/', views.schedule_bus_details, name='bus_details'),
  path('booking-details/<int:id>/', views.booking_details, name='booking_details'),

  # ======== Booking Management ==========
  path('booking-management/', views.booking_management, name='booking_list'),
  path('booking-status-update/<int:booking_id>/',views.booking_status_update,name="update_booking_status"),
  path('booking-reservation/update/<int:id>/', views.reservationBooking_update, name="update_reservation"),
  path('booking-resevation/delete/<int:id>/',views.delete_vehicle_reservation_booking,name="delete_reservation"),

  # ======== Report Analysis ==========
  path('reports/', views.report_analysis_view, name='report_analysis'),

  # ======== System Settings ==========
  path('settings/', views.system_settings_view, name='system_settings'),

  # ======== Payment Management ==========
  path('bus-bookings-payment/', views.bus_payment_details, name='bus_payments_details'),
  path('bus-earning-details/<int:bus_id>/', views.bus_earning_details_schedule, name='bus_earnings'),
  path('bus-earning-payment/<int:schedule_id>/',views.bus_earning_payment,name="schedule_payment_details"),
  
  
  
  path('reservation-payment/', views.reservation_payment_details, name='reservation_payment_details'),
  path('vehicle-earnings-details/<int:vehicle_id>/',views.vehicle_reservation_earings_details,name="vehicle_earning_details"),
  path('reservation-details/<int:id>/',views.vehicle_details_payment,name="vehicle_details_payment"),
  
  
  # ================ Paymant adn trasctions ===============
  path('payments/',views.payment_list,name="payment_list"),




  # ========== trips details =========
  path('all-trips/',views.all_trips,name="all_trips"),

  


# ========= Notification ==========

  path('all/notification/', views.all_notification, name='all_notification'),
  path('add-notification/', views.add_notification, name='add_notification'),
  path('edit-notification/<int:id>/', views.edit_notification, name='edit_notification'),
  path('notification/delete/<int:id>/', views.delete_notification, name='delete_notification'),
  
  # ======== Privecy ============
  path('privacy/',views.privacy,name='privacy')
  
]
