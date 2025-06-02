from bus_booking.celery import shared_task



@shared_task
def release_unpaid_seat(booking_id, schedule_id):
    """
    Release a specific seat if the user doesn't complete payment within the timeout period.
    
    Args:
        booking_id: ID of the booking
        seat_id: ID of the seat to release
    """
    from .models import Booking,Schedule
    from bus.models import SeatLayoutBooking

    
    try:
        print("--------- Redis -----------")
        booking = Booking.objects.get(id=booking_id)
        schedule = Schedule.objects.get(id=schedule_id)

        try:
            seat_layout = SeatLayoutBooking.objects.get(schedule=schedule)
            seat_layout.mark_seat_available(booking.seat)
        except SeatLayoutBooking.DoesNotExist:
            print(f"SeatLayout Booking not found for bus: {booking.bus}")
            seats = booking.seat
            schedule.available_seats += len(booking.seat)
            schedule.save()
            print(f"Released unpaid seat {seats} for booking {booking_id}")

        booking.delete()  

    except Booking.DoesNotExist:
        print(f"Booking {booking_id} not found")
    except Schedule.DoesNotExist:
        print(f"Schedule {schedule_id} not found")


