from bus_booking.celery import shared_task


@shared_task
def release_unpaid_seat(booking_id, seat_id):
    """
    Release a specific seat if the user doesn't complete payment within the timeout period.
    
    Args:
        booking_id: ID of the booking
        seat_id: ID of the seat to release
    """
    from .models import Booking, Seat, BusLayout
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Only release the seat if the booking is still in pending status
        if booking.booking_status == 'pending':
            try:
                # Find the specific seat and make it available again
                seat = Seat.objects.get(seat_number=seat_id, bus=booking.bus)
                seat.status = 'available'
                seat.save()
                
                # Update the bus layout if it exists
                try:
                    bus_layout = BusLayout.objects.get(bus=booking.bus)
                    bus_layout.update_seat_status(seat_id, 'available')
                except BusLayout.DoesNotExist:
                    print(f"BusLayout not found for bus: {booking.bus}")
                
                # Update the booking's seat list to remove this seat
                updated_seats = [s for s in booking.seat if s != seat_id]
                booking.seat = updated_seats
                
                # If no seats left, mark the booking as canceled
                if not updated_seats:
                    booking.booking_status = 'canceled'
                
                booking.save()
                
                print(f"Released unpaid seat {seat_id} for booking {booking_id}")
            except Seat.DoesNotExist:
                print(f"Seat {seat_id} not found for booking {booking_id}")
    except Booking.DoesNotExist:
        print(f"Booking {booking_id} not found")
