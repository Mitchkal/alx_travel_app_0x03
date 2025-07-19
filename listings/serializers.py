from rest_framework import serializers
from .models import Booking, Review, Listing, Payment


class BookingSerializer(serializers.ModelSerializer):
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


class ListingSerializer(serializers.ModelSerializer):
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


class ReviewSerializer(serializers.ModelSerializer):
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


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for payments model
    """

    class Meta:
        model = Payment
        fields = [
            "payment_id",
            "booking_id",
            "amount",
            "created_at",
            "payment_method",
            "transaction_id",
            "status",
        ]
