from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing, Booking, Review, Payment
from django.contrib.auth.models import User
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer, UserInfoSerializer, PaymentSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os
import requests


CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY")
CHAPA_BASE_URL = os.getenv("CHAPA_BASE_URL")
FRONTEND_PAYMENT_REDIRECT = os.getenv("FRONTEND_PAYMENT_REDIRECT")
HEADERS = {
    "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
    "Content-Type": "application/json",
}


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserInfoSerializer

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

    def get_permissions(self):
        """ Require authenticaion only whe creating/updating listings
            Anyone can view listing
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)
    
    def perform_destroy(self, instance):
        """Only the owner of the listing can delete it"""
        user = self.request.user
        if instance.host != user:
            raise PermissionDenied("You can only delete your own listings.")
        instance.delete()


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # Displays all bookings for a specific listing
    filterset_fields = ['listing']  # Add the filter for: GET /api/bookings/?listing=<listing_id>

    """Adds the filter by listing in Swagger documentation"""
    # Overrides list method only to attach Swagger metadata
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'listing',                 # name of the query param
            openapi.IN_QUERY,          # it's in the URL query string
            description="Filter bookings by listing ID",
            type=openapi.TYPE_STRING   # String ID 
        )
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        # When connected to the auth service, make sure to use user.role
        # if hasattr(user, 'role') and user.role == 'host':
        if user.is_staff:
            # Host sees bookings for their listings only
            return Booking.objects.filter(listing__host=user)
        # Guest sees their own bookings
        return Booking.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing = serializer.validated_data["listing"]
        days = (serializer.validated_data["end_date"] - serializer.validated_data["start_date"]).days + 1

        booking = serializer.save(
            user=request.user,
            total_price=listing.price_per_night * days,
            status="pending"
        )

        # create payment + get Chapa URL
        payment = Payment.objects.create(
            booking_reference=str(booking.booking_id),
            amount=booking.total_price,
            status="Pending",
        )

        r = requests.post(
            f"{CHAPA_BASE_URL}/transaction/initialize",
            json={
                "amount": str(payment.amount),
                "currency": "ETB",
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "tx_ref": payment.booking_reference,
                "return_url": FRONTEND_PAYMENT_REDIRECT,
            },
            headers=HEADERS,
        ).json()

        data = r.get("data", {})
        payment.transaction_id = data.get("id") or data.get("tx_ref") or "N/A"
        payment.save()

        checkout_url = data.get("checkout_url")

        return Response({
            **serializer.data,
            "payment_url": checkout_url
        }, status=201)
    
    def perform_destroy(self, instance):
        user = self.request.user
        if instance.user != user:
            raise PermissionDenied("You can only delete your own booking.")
        if instance.status == "confirmed":
            raise PermissionDenied("Cannot delete a confirmed booking. Set status to canceled instead.")
        instance.delete()


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        """ Require authenticaion only whe creating/updating reviews
            Anyone can view reviews
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Reviews is nested in listings: api/listings/<listing_pk>/reviews/"""
        listing_id = self.kwargs.get('listing_pk')
        if listing_id:
            return Review.objects.filter(listing_id=listing_id)
        return Review.objects.all()

    def perform_create(self, serializer):
        listing_id = self.kwargs.get('listing_pk')
        serializer.save(user=self.request.user, listing_id=listing_id)
    
    def perform_destroy(self, instance):
        user = self.request.user
        if instance.user != user:
            raise PermissionDenied("You can only delete your own review.")
        instance.delete()


@api_view(["POST"])
def initiate_payment(request):
    """Payment initiation view using Chapa API"""
    booking_ref = request.data["booking_reference"]
    amount = request.data["amount"]
    email = request.data["email"]
    first_name = request.data["first_name"]
    last_name = request.data["last_name"]

    payment = Payment.objects.create(
        booking_reference=booking_ref,
        amount=amount,
        status="Pending",
    )

    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "tx_ref": booking_ref,
        "callback_url": request.build_absolute_uri("/api/payments/verify/"),
        "return_url": FRONTEND_PAYMENT_REDIRECT,
    }

    response = requests.post(
        f"{CHAPA_BASE_URL}/transaction/initialize",
        json=payload,
        headers=HEADERS,
    ).json()

    if response.get("status") == "success":
        payment.transaction_id = response["data"]["id"]
        payment.save()
        return Response(
            {"payment_url": response["data"]["checkout_url"]},
            status=status.HTTP_200_OK,
        )

    payment.status = "Failed"
    payment.save()
    return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def verify_payment(request):
    """View to verify payment status using Chapa API"""
    tx_ref = request.GET.get("tx_ref")

    payment = Payment.objects.get(booking_reference=tx_ref)

    response = requests.get(
        f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
        headers=HEADERS,
    ).json()

    if response.get("status") == "success":
        payment.status = "Completed"
        payment.save()
        return Response({"detail": "Payment verified"}, status=200)

    payment.status = "Failed"
    payment.save()
    return Response({"detail": "Payment failed"}, status=400)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer