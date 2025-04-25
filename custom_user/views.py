
from bus.models import SeatLayoutBooking
from booking.models import Booking, Payment, BusReservationBooking
from route.models import Route, Schedule,  CustomerReview,Notification
from  custom_user.serializers import CustomUserSerializer
from route.serializers import RouteSerializer,BookingSerializer, ScheduleSerializer,CustomReviewSerializer,PaymentSerializer,BusReservationBooking,VechicleReservationBookingSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from rest_framework import status


# ====== User Dashboard Data =========

class UserDashboardView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]

    def get(self,request):
        print(request.user)
        user=request.user
        data={}
        data["total_booking"]=Booking.objects.filter(user=user).count()
        data["total_reviews"]=CustomerReview.objects.filter(user=user).count()
        data["total_reservation"]= BusReservationBooking.objects.filter(user=user).count()
        total_payment=0
        total_payment=Booking.objects.filter(user=user,booking_status="booked").count()
        total_payment=BusReservationBooking.objects.filter(user=user,status="booked").count()
        
        data["total_payment"]=total_payment
        recent_booking=Booking.objects.filter(user=user).order_by('-id')[:5]
        recent_reviews=CustomerReview.objects.filter(user=user).order_by('-id')[:5]

        recent_booking_serializer=BookingSerializer(recent_booking,many=True)
        recent_reviews_serializer=CustomReviewSerializer(recent_reviews,many=True)

        return Response({"success":True,"data":data,"recent_booking":recent_booking_serializer.data,"recent_reviews":recent_reviews_serializer.data},status=200)

        # ========= User Profile ===========
class UserUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
                user = request.user
                serializer = CustomUserSerializer(user)
                return Response({"success": True, "data": serializer.data})

    def patch(self, request):
                user = request.user
                serializer = CustomUserSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"success": True, "data": serializer.data}, status=200)
                return Response({"success": False, "error": serializer.errors}, status=400)


        # ====== Available Schedule for User =========
class AvailableSchedule(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
                schedules = Schedule.objects.filter(departure_time__gte=now())
                serializer = ScheduleSerializer(schedules, many=True)
                return Response({"success": True, "data": serializer.data}, status=200)


# ======== Booked Seat for User =========
class BookedSeat(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
                user = request.user
                bookings_seat = Booking.objects.filter(user=user).order_by('-booked_at')
                serializer_seat = BookingSerializer(bookings_seat, many=True)
                
                reserve = BusReservationBooking.objects.filter(user=user).order_by('-created_at')
                serializer_reserve = VechicleReservationBookingSerializer(reserve, many=True)
            
                return Response({"success": True, "booking_seat": serializer_seat.data, "booking_reserve": serializer_reserve.data}, status=200)


        # ======== User's Favorite Routes =========
class FavoriteRoutesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
                user = request.user
                favorite_routes = Route.objects.filter(favorites__user=user)
                serializer = RouteSerializer(favorite_routes, many=True)
                return Response({"success": True, "data": serializer.data}, status=200)


        # ======== User's Payment History =========
class PaymentHistoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
                user = request.user
                payments = Payment.objects.filter(user=user).order_by('-created_at')
                serializer=PaymentSerializer(payments,many=True)
                return Response({"success": True, "data":serializer.data}, status=200)




# ==================
# User Booking Paymnet
# ==================

import requests
import json
import uuid
from django.db import transaction

class UserBookingPaymentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():  
                user = request.user
                print(user)
                print(request.data)

                seat = request.data.get('seat')  
                schedule_id = request.data.get('schedule_id')
                schedule_obj = Schedule.objects.get(bus=schedule_id)

                count = len(seat)
                schedule_obj.available_seats -= count
                schedule_obj.save()

                #  Calculate total price
                total_price = schedule_obj.price * count
                print(f"Total Price: {total_price}")

                #  Mark seats as booked in bus layout
                bus_layout = SeatLayoutBooking.objects.get(schedule=schedule_obj)
                bus_layout = bus_layout.layout_data
                bus_layout.mark_seat_booked(seat)

                #  Create booking entry
                booking_obj = Booking.objects.create(
                    user=user,
                    seat=seat,
                    bus=schedule_obj.bus,
                 
                    schedule=schedule_obj
                )
                
                # Khalti Payment Integration
                payload = json.dumps({
                    "return_url": "https://example.com/payment-success",
                    "website_url": "https://example.com",
                    "amount": float(total_price)*100,
                    "booking_id": str(uuid.uuid4()), 
                    "purchase_order_id":booking_obj.id,
                    "purchase_order_name": "Bus Ticket Booking",
                    "customer_info": {
                        "name": user.full_name
                    }
                })

                headers = {
                    'Authorization': "key c3ace8e77db241119661f858acd5f6de",
                    'Content-Type': 'application/json',
                }

                response = requests.post("https://a.khalti.com/api/v2/epayment/initiate/", headers=headers, data=payload)
                print(response.content)
                new_res = response.json()

                if "payment_url" not in new_res:
                    return Response({'success': False, 'error': 'Khalti Payment Failed'}, status=status.HTTP_400_BAD_REQUEST)

             
                data = {
                    'bus_number': booking_obj.bus.bus_number,
                    'source': booking_obj.bus.route.source,
                    'destination': booking_obj.bus.route.destination,
                    'booking_status': booking_obj.booking_status,
                    'seat': booking_obj.seat,
                    'booked_at': booking_obj.booked_at,
                    'total_price': total_price,
                    'total_seat': count,
                    'pidx':new_res.get('pidx',''),
                    'payment_url': new_res.get('payment_url', ''),
                    'booking_id': booking_obj.id
                }

                return Response({'success': True, 'data': data}, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response({'success': False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    


    
# ===== User Payment ===========
class UserPayment(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def post(self,request):
        try:
        
            user=request.user
            total_amount=request.data.get('amount')
            booking_id=request.data.get('booking_id')
            try:
                booking_obj = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                return Response({'success': False, 'error': 'Booking not found'}, status=400)
            transaction_id = request.data.get('transaction_id')
            Payment.objects.create(user=user, price=total_amount, payment_status="completed", transaction_id=transaction_id, booking=booking_obj)
            
           
            booking_obj.booking_status = "booked"
            booking_obj.save()
            message=f"Thank you ! Your seat has been booked on bus {booking_obj.schedule.bus.bus_number}. Have a safe journey !"
            Notification.objects.create(type="booking",user=request.user,title="Booking",message=message)

            return Response({'success':True,'message':"Successfully payment"},status=200)
            
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)



# ========= User Review ==========
class UserReviews(APIView):
    def get(self,request):
        try:
            user=request.user
            user_reviews=CustomerReview.objects.filter(user=user)
            serializer=CustomReviewSerializer(user_reviews,many=True)
            return Response({'success':True,'data':serializer.data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        


# ===============================
# ====== SubAdmin ==============
# ==============================


class SubAdminApiView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]

    def get(self, request):
        print(request.user)
        user = request.user
        transportation_company = getattr(user, "transportation_company", None)

        if not transportation_company:
            return Response({"success": False, "error": "User is not associated with a transportation company"}, status=400)

        print("Name",transportation_company)
        
        data = {
            "total_booking": Booking.objects.filter(user=user).count(),
            "total_reviews": CustomerReview.objects.filter(user=user).count(),
            "total_reservation": BusReservationBooking.objects.filter(user=user).count(),
            "total_payment": (
                Booking.objects.filter(booking_status="booked").count() +
                BusReservationBooking.objects.filter(bus_reserve__transportation_company=transportation_company, status="booked").count()
            ),
        }

        recent_booking = Booking.objects.filter(user=user).order_by('-id')[:5]
        recent_reviews = CustomerReview.objects.filter(user=user).order_by('-id')[:5]

        recent_booking_serializer = BookingSerializer(recent_booking, many=True)
        recent_reviews_serializer = CustomReviewSerializer(recent_reviews, many=True)

        return Response({
            "success": True,
            "data": data,
            "recent_booking": recent_booking_serializer.data,
            "recent_reviews": recent_reviews_serializer.data
        }, status=200)