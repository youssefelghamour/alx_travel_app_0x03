from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_booking_confirmation_email(to_email, booking_id):
    """shared task function to send a booking confirmation email upon booking creation"""
    send_mail(
        subject='Booking Confirmation',
        message=f'Your booking #{booking_id} has been confirmed.',
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[to_email],
        fail_silently=False,
    )
