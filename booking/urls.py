from django.contrib import admin
from django.urls import path,include

from . import views
urlpatterns = [
    
     # ======== Admin Dashboard ==========
    path('admin_dashboard/',views.AdminDashboardData.as_view()),
    
    # ====== Admin Profile ======
    
    path('admin_profile/',views.AdminProfile.as_view()), 
    path('admin_profile_update/',views.AdminProfile.as_view()),
    
    # ===== Admin Ticket Counter =========
    path('admin_ticketcounter/',views.TicketCounterView.as_view()),
    path('admin_ticketcounter_add/',views.TicketCounterView.as_view()),
    path('admin_ticketcounter_update/<id>/',views.TicketCounterView.as_view()),
    path('admin_ticketcounter_delete/<id>/',views.TicketCounterView.as_view()),
    
    # ======= user Management ==========
    path('admin_userlist/',views.UserListView.as_view()),
    # path('admin_usrlist_add/')
    path('admin_userlist_update/<id>/',views.UserListView.as_view()),
    path('admin_userlist_delete/<id>/',views.UserListView.as_view()),
    
    # ======= Driver managment =========
    path('admin_driverlist/',views.DriverListView.as_view()),
    path('admin_driverlist_add/',views.DriverListView.as_view()),
    path('admin_driverlist_update/<id>/',views.DriverListView.as_view()),
    path('admin_driverlist_delete/<id>/',views.DriverListView.as_view()),
    
    
    # ===== Staff management ========
    path('admin_stafflist/',views.StaffListView.as_view()),
    path('admin_stafflist_add/',views.StaffListView.as_view()),
    path('admin_stafflist_update/<id>/',views.StaffListView.as_view()),
    path('admin_stafflist_delete/<id>/',views.StaffListView.as_view()),
    
    
    # ===== Bus management ========
    path('admin_buslist/',views.BusListView.as_view()),
    path('admin_buslist_add/',views.BusListView.as_view()),
    path('admin_buslist_update/<id>/',views.BusListView.as_view()),
    path('admin_buslist_delete/<id>/',views.BusListView.as_view()),
    
   
    
    # ======  Schedule ======
    path('admin_schedulelist/',views.ScheduleView.as_view()),
    path('admin_schedulelist_add/',views.ScheduleView.as_view()),
    path('admin_schedulelist_update/<int:id>/',views.ScheduleView.as_view()),
    path('admin_schedulelist_delete/<int:id>/',views.ScheduleView.as_view()),
    
    # ==== Bus details of schedule =========
    path('admin_schedule_bus_details/<int:id>/',views.BusDetailsScheduleApiView.as_view()),
    
    # ======== route ========
    path('admin_routelist/',views.RouteApiView.as_view()),
    path('admin_routelist_add/',views.RouteApiView.as_view()),
    path('admin_routelist_update/<int:id>/',views.RouteApiView.as_view()),
    path('admin_routelist_delete/<int:id>/',views.RouteApiView.as_view()),
    
    # =====  Route to all Bus List =============
    path('admin_route_buslist/<int:id>/',views.RouteBusListAPiView.as_view()),
    
    
    
    # ====== Booking ========
    path('admin_bookinglist/',views.BookingAPiView.as_view()),
    path('admin_bookinglist_update/<int:id>/',views.BookingAPiView.as_view()),
    
    # ===  One user Booking details =========
    path('admin_user_booking_details/<int:id>/', views.BookingScheduleOneUserDetails.as_view()),
    
    # ========Vehicle Reservetion ===========
    path('admin_vehiclereservationlist/',views.VechicleReservationView.as_view()),
    path('admin_vehiclereserve_add/',views. VechicleReservationView.as_view()),
    path('admin_vehiclereserve_update/<int:id>/',views. VechicleReservationView.as_view()),
    path('admin_vehiclereserve_delete/<int:id>/',views. VechicleReservationView.as_view()),
    
    
    # =========Vechicle Type =========
    path('admin_vehicletype/', views.VehicleTypeViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('admin_vehicletype/<int:pk>/', views.VehicleTypeViewSet.as_view({ 'patch': 'update', 'delete': 'destroy'})),
    
    #============ Payment ==========
    path('admin_paymentlist/',views.PaymentApiView.as_view()),
    
    # ======== Rate========
    path('admin_rate_add/<int:id>/',views.RateApiView.as_view()),
    
    
    
    #============ Report and analysis ============
    path('admin_reportlist/',views.ReportAnalysisApiView.as_view()),
    
    
    # ========= Setting =============
    path('admin_settings/',views.SettingsApiView.as_view()),
    path('admin_settings_update/<int:id>/',views.SettingsApiView.as_view())
    
    
    
]