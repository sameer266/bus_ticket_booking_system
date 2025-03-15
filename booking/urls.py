from django.contrib import admin
from django.urls import path,include

from . import views
urlpatterns = [
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
    path('admin_buslist_add',views.BusListView.as_view()),
    path('admin_buslist_update/<id>/',views.BusListView.as_view()),
    path('admin_buslist_delete/<id>/',views.BusListView.as_view())
    
    
]