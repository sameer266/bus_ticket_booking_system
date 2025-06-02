from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include

from . import views
urlpatterns = [
    
    # ===== User Dashboard ========
    path('user_dashboard/', views.UserDashboardView.as_view()),
    
    # ======= User Profile =========
    path('user_profile/', views.UserUpdateView.as_view()),
    path('user_profile_update/', views.UserUpdateView.as_view()),

    # ====== Available Schedule for User =========
    path('available_schedule/', views.AvailableSchedule.as_view()),

    # ======== Booked Seat for User =========
    path('user_booking_list/', views.BookedSeat.as_view()),
    

    # ======== User's Favorite Routes =========
    path('favorite_routes/', views.FavoriteRoutesView.as_view()),


    # ========= User's Booking process ========
    path('user_booking_add/',views.UserBookingPaymentView.as_view()),
    
    # ========== User Review ============
    path('user_reviews/',views.UserReviews.as_view()),
    
    # ========== USer payment ===============
    path('user_payment/',views.UserPayment.as_view()),


    # ======== User's Payment History =========
    path('payment_history/', views.PaymentHistoryView.as_view()),
    
    # ====== Khalti paymnet ===========
    # path('khalti-initiate/',views.InitiateKhaltiPayment.as_view(),name="initiate"),
    #path('khalti-verify/',views.VerifyKhalti.as_view(),name="verify"),
    
    # ====================
    # Sub Admin 
    #======================
    path('subadmin_dashboard/',views.SubAdminApiView.as_view())
    
]


# ================== Static Files in Debug Mode ==================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)