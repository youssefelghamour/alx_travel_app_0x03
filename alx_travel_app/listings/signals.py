from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
from .views import initiate_payment
from rest_framework.test import APIRequestFactory
from .payments import start_payment


factory = APIRequestFactory()
"""
@receiver(post_save, sender=Booking)
def create_payment(sender, instance, created, **kwargs):
    ""Signal to initiate payment when a booking is created""
    if created:
        start_payment(instance)
"""