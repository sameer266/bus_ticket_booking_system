       
from django.db.models import Count
from datetime import datetime

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

class FilterRoute(APIView):
    def get(self,request):
        try:
            source=request.query_params.get('source')
            destination=request.query_params.get('destination')
            departure_time=request.Query_params.get('departure_time')
            departure_time=datetime.strptime(departure_time)
            route=Route.objects.filter(source=source,destination=destination)
            schedule=Schedule.objects.get(route=route)
            serializer=ScheduleSerializer(schedule,many=True)
            if schedule:
                return Response({"success":True,"data":serializer.data},status=200)
        
        except schedule.DoesNotExist:
            return Response({"success":False,"error":"No Schedule found"},status=401)
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)



class PopularRoutes(APIView):
    def get(self):
        try:
            top_routes = Route.objects.values('source','destination') \
                        .annotate(route_count=Count('id')) \
                        .order_by('-route_count')[:4] 
            return Response({'success':True,'data':top_routes},status=200)
        
        except Exception as e:
            return Response({"success":False,"error":str(e)},status=400)    