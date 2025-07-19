from django.shortcuts import render
from django.http import HttpResponse
from datetime import date
from .models import Booking, Listing, Payment
from rest_framework import viewsets
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework.response import Response
from django.conf import settings
import uuid
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


# from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from .filters import ListingFilter


class ListingViewSet(viewsets.ModelViewSet):
    """
    Viewset for Travel listings
    """

    serializer_class = ListingSerializer
    queryset = Listing.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filterset_class = ListingFilter

    def get_queryset(self):
        """
        queryset to display all available listings
        """
        listings = Listing.objects.all()
        print("Listing queryset:", listings)
        # return Response(listings)
        return listings

    def perform_create(self, serializer):
        """
        Allow only authenticated users assigned as hosts
        to create a listing
        """
        serializer.save(host=self.request.user)

    def perform_update(self, serializer):
        """
        Allow only hosts to update listings
        """
        if self.request.user != serializer.instance.host:
            raise PermissionDenied("You do not have permission to edit this listing")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Allow Listing deletion only if the user is a host
        """
        if self.request.user != instance.host:
            raise PermissionDenied("You have to be the host to edit this listing")
        instance.delete()

    # def create(self, request):
    #     """
    #     creates the views
    #     """
    #     pass


class BookingViewSet(viewsets.ModelViewSet):
    """
    Viewsets for the Bookings
    """

    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "property_id", "start_date", "end_date"]

    def get_queryset(self):
        """
        get query set
        """
        user = self.request.user

        # return Booking.objects.all()
        if user:
            # for hosts return bookings related to their listing
            # return Booking.objects.filter(property_id__host=user)
            return Booking.objects.all()
        elif user.is_anonymous:
            # test t return all bookings
            return Booking.objects.all()
        else:
            # for regular users return theri own bookings only
            # return Booking.objects.filter(user_id=user)
            return Booking.objects.all()

    def perform_create(self, serializer):
        listing = serializer.validated_date["property_id"]
        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # validate he future dates
        if start_date < date.now() or start_date >= end_date:
            raise ValidationError("Invalid booking dates")

        # check for overlapping bookings
        overlapping = Booking.objects.filter(
            property_id=listing,
            start_date_lt=end_date,
            end_date_gt=start_date,
            status__in=["PENDING", "CONFIRMED"],
        ).exists()
        if overlapping:
            raise ValidationError("Listing already booked for these dates")

    def perform_update(self, serializer):
        """
        Allow updating satus changes and future date changes
        """
        instance = self.get_object()

        if instance.status == "CANCELLED" or instance.start_date < date.today():
            raise ValidationError("You cannot update past or cancelled bookings")

        serializer.save()

    def trigger_email_task(self, request):
        """
        Trigger the email task after booking creation
        """
        from .tasks import send_booking_confirmation_email

        booking = self.get_object()
        send_booking_confirmation_email.delay(booking)
        return render(request, "booking_confirmation.html", {"booking": booking})

    @action(detail=True, methods=["patch"])
    def cancel(self, request, pk=None):
        """
        for cancelling a booking
        """
        booking = self.get_object()

        if booking.user_id != request.user:
            raise PermissionDenied("You cannot cancel this booking.")

        booking.status = "CANCELLED"
        booking.save()
        return Response({"status": "cancelled"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def confirm(self, request, pk=None):
        """
        Allows listing host to confirm booking
        """
        booking = self.get_object()

        if booking.property_id.host != request.user:
            raise PermissionDenied("Only the host can confirm this booking")

        if booking.status != "PENDING":
            raise ValidationError("Only pending bookings can be confirmed.")

        booking.status = "CONFIRMED"
        booking.save()
        return Response({"status": "confirmed"}, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Viewset for handling payments
    """

    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Allow authenticated users to create payments
        """
        booking = serializer.validated_date("booking_id")
        if booking.user_id != self.request.user:
            raise PermissionDenied("You can only pay for your own bookings")
        with transaction.atomic():
            # Generate unique transaction reference
            tx_ref = f"{uuid.uuid4().hex[:10]}-{booking.booking_id}"
            payment = serializer.save(
                transaction_id=tx_ref,
                status=Payment.Status.PENDING,
            )
            # prepare Chapa Payment data
            chapa_data = {
                "amaount": str(payment.amount),
                "currency": "USD",
                "tx_ref": tx_ref,
                "email": payment.booking_id.user_id.email,
                "first_name": str(payment.booking_id.user_id.first_name) or "User",
                "last_name": str(payment.booking_id.user_id.last_name) or "User",
                "phone_number": str(payment.booking_id.user_id.phone_number)
                or "000-000-0000",
                "return_url": self.request.build_absolute_url(
                    "/api/payments/callback/"
                ),
                "callback_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
                "title": f"Payment for Booking {booking.booking_id}",
                "description": f"Payment for booking {booking.booking_id} at {booking.property_id.name}",
            }
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
                "Content-Type": "application/json",
            }
            try:

                response = requests.post(
                    f"{settings.CHAPA_API_URL}/transactions/initialize",
                    json=chapa_data,
                    headers=headers,
                )
                response.raise_for_status()
                chapa_response = response.json()
                if chapa_response.get("status") == "success":
                    # save checkout url
                    payment.checkout_url = chapa_response.get("data", {}).get(
                        "checkout_url"
                    )
                    payment.save()
                    return Response(
                        {
                            "message": "Payment initiated successfully",
                            "checkout_url": payment.checkout_url,
                            "payment_id": str(payment.payment_id),
                            ", ": tx_ref,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    payment.status = Payment.Status.FAILED
                    payment.save()
                    return Response(
                        {
                            "message": "Payment initiation failed",
                            "error": chapa_response.get(
                                "message", "Failed to initiate payment"
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except requests.exception.RequestExcepption as e:
                payment.status = Payment.Status.FAILED
                payment.save()
                return Response(
                    {
                        "message": "Payment initiation failed",
                        "error": f"Payment initialization failed: {str(e)}",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


def index(request):
    return HttpResponse("Hello from Listings!")


@csrf_exempt
def payment_callback(request):
    """
    Handles the chapa payment callback
    """
    if request.method == "POST":
        # verify webhook request
        try:
            chapa_tx_ref = request.POST.get("tx_ref")
            payment = Payment.objects.get(transaction_id=chapa_tx_ref)

            # verify payment with Chapa
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
                "Content-Type": "application/jsom",
            }
            response = requests.get(
                f"{settings.CHAPA_API_URL}/transactions/verify/{chapa_tx_ref}",
                headers=headers,
            )
            response.raise_for_status()
            chapa_response = response.json()

            if chapa_response.get("status") == "success":
                payment.status = Payment.Status.COMPLETED
                payment.save()
                return JsonResponse(
                    {"status": "success", "message": "Payment Verified"}
                )
            else:
                payment.status = Payment.Status.Failed
                payment.save()
                return JsonResponse(
                    {"status": "failed", "messahe": "Payment verification failed"}
                )

        except Payment.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Payment not found"}, status=404
            )
        except requests.RequestException as e:
            return JsonResponse(
                {"status": "error", "message": f"Error verifying payment: {str(e)}"},
                status=500,
            )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=405
    )


def health_check(request):
    """
    simple health check endpoint
    """
    return JsonResponse({"status": "ok", "message": "API is healthy"}, status=200)
