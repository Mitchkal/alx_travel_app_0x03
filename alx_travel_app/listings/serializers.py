from rest_framework import serializers
from .models import Booking, Review, Listing


class BookingSerializer(serializers.Serializer):
    """
    Serializer model for the Bookings
    """

    class Meta:
        model = Booking
        fields = [
            "booking_id",
            "property_id",
            "user_id",
            "start_date",
            "end_date",
            "status",
            "total_price",
            "created_at",
        ]
        read_only_fields = ["total_price"]


class ListingSerializer(serializers.Serializer):
    """
    Serializer for listings
    """

    class Meta:
        model = Listing
        fields = [
            "property_id",
            "host",
            "name",
            "description",
            "location",
            "price_per_night",
            "amenities",
            "capacity",
        ]


class ReviewSerializer(serializers.Serializer):
    """
    Serializer for reviews
    """

    class Meta:
        model = Review
        fields = [
            "review_id",
            "property_id",
            "user_id",
            "rating",
            "comment",
        ]
