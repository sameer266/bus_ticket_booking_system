from route.models import Route,Schedule,Trip
from .serializers import RouteSerializer,ScheduleSerializer
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response


class AllRoutes(APIView):
    def get(self,request):
        route= Route.objects.all()
        serializer=RouteSerializer(route,many=True)
        return Response({"success":True,"data":serializer.data},status=200)
        
class AllSchedule(APIView):
    def get(self,request):
        schedule=Schedule.objects.all()
        serializer=ScheduleSerializer(schedule,many=True)
        return Response({"success":True,"data":serializer.data},status=200)
    