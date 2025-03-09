
from django.urls import path

from . import views




urlpatterns = [
    path('all_routes/',views.AllRoutes.as_view()),
    path('all_schedule/',views.AllSchedule.as_view())
    
]