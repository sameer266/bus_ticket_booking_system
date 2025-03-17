from bus_booking.celery import shared_task


@shared_task
def release_unpaid_seat(booking_id):
    from .models import Booking
    """Release seat if the user doesn't pay within 10 minutes."""
    try:
        booking = Booking.objects.get(id=booking_id)
        if not booking.paid:  # If payment is not completed
            booking.seat.status = 'available'  # Make seat available again
            booking.seat.save()
            booking.booking_status = 'canceled'  # Cancel the booking
            booking.save()
    except Booking.DoesNotExist:
        pass  # Ignore if the booking is already deleted
