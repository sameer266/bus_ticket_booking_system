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
    
    # ======= user amangement ==========
    path('admin_userlist/',views.UserListView.as_view()),
    # path('admin_usrlist_add/')
    path('admin_userlist_update/<id>/',views.UserListView.as_view()),
    path('admin_userlist_delete/<id>/',views.UserListView.as_view()),
    
    
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
    
    
    # ======== route ========
    path('admin_routelist/',views.RouteApiView.as_view()),
    path('admin_routelist_add/',views.RouteApiView.as_view()),
    path('admin_routelist_update/<int:id>/',views.RouteApiView.as_view()),
    path('admin_routelist_delete/<int:id>/',views.RouteApiView.as_view()),
    
    
    # ====== Booking ========
    path('admin_bookinglist/',views.BookingAPiView.as_view()),
    path('admin_bookinglist_update/<int:id>/',views.BookingAPiView.as_view()),
    
    
    
    #============ Payment ==========
    path('admin_paymentlist/',views.PaymentApiView.as_view()),
    
    # ======== Rate========
    path('admin_rate_add/<int:id>/',views.RateApiView.as_view()),
    
    #============ Report and analysis ============
    
    path('admin_reportlist/',views.ReportAnalysisApiView.as_view()),
    
]