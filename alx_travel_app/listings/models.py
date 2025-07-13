from django.db import models
import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from django.utils.timezone import now
from django.core.exceptions import ValidationError


# Create your models here.
class Listing(models.Model):
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # host = models.CharField(max_length=200)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # host_id = models.ForeignKey(
    #     settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings"
    # )
    name = models.CharField(max_length=100, validators=[MinValueValidator(5)])
    description = models.TextField(max_length=500)
    location = models.CharField(max_length=200)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(10000)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amenities = models.TextField()
    # amenities = models.JSONField(default=list)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # availability = models.TextField()

    def get_amenities(self):
        """
        helper method to get amenities
        """
        return json.loads(self.amenities) if self.amenities else []

    class Meta:
        indexes = [models.Index(fields=["location"])]

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    property_id = models.ForeignKey(
        Listing, related_name="bookings", on_delete=models.CASCADE
    )
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="bookings", on_delete=models.CASCADE
    )
    start_date = models.DateField()
    end_date = models.DateField()
    guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_date__lt=models.F("end_date")),
                name="start_before_end",
            ),
            # models.CheckConstraint(
            #     check=models.Q(start_date__gte=models.functions.Now()),
            #     name="future_dates",
            # ),
        ]

    def clean(self):
        if self.start_date < now():
            raise ValidationError("Start date must be in the future")

    def __str__(self):
        return f"Booking {self.booking_id} for {self.property_id}"


class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property_id = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="reviews"
    )
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=132, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "property_id"],
                name="unique_review_per_user_property",
            )
        ]

    def __str__(self):
        return f"Review {self.review_id} for {self.property_id}"


# Create your models here.
