import requests, os
from .models import Payment

def start_payment(booking):
    Payment.objects.create(
        booking_reference=str(booking.booking_id),
        amount=booking.total_price,
        status="Pending",
    )