from django.shortcuts import render
from django.http import HttpResponse
from datetime import date
from .models import Booking, Listing
from rest_framework import viewsets
from .serializers import ListingSerializer, BookingSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.exceptions import PermissionDenied

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
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = ListingFilter

    def get_queryset(self):
        """
        queryset to display all available listings
        """
        return Listing.objects.all()

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
        return Booking.objects.all()
        # if self.request.user.is__host:
        #     # for hosts return bookings related to their listing
        #     return Booking.objects.filter(property_id__host=self.request.user)
        # else:
        #     # for regular users return theri own bookings only
        #     return Booking.objects.filter(user_id=self.request.user)

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

    @action(detail=True, methods=["patch"])
    def cancel(self, request, pk=None):
        """
        for acncelling a booking
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


def index(request):
    return HttpResponse("Hello from Listings!")
