#!/usr/bin/env python3
"""
seed script to
seed Listings table
"""
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing
from django.db import IntegrityError, DatabaseError
import json


class Command(BaseCommand):
    help = "Seeds the database with sample listings data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seeding...")

        # Get or create a host user
        User = get_user_model()
        try:
            host, created = User.objects.get_or_create(
                email="host@example.com",
                defaults={"username": "localhost"},
            )
            if created:
                host.set_password("12121963")  # Hash the password
                host.save()
                self.stdout.write(self.style.SUCCESS("Created host user"))
            else:
                self.stdout.write(self.style.WARNING("Host user already exists"))
        except DatabaseError as e:
            self.stdout.write(self.style.Error(f"Database error creating host: {e}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected Error creating host: {e}"))
            return

        # Sample listings data
        sample_listings = [
            {
                "name": "Cozy Beach Cottage",
                "description": "A charming cottage by the sea.",
                "location": "Malibu, CA",
                "price_per_night": 150.00,
                "amenities": ["WiFi", "Beach Access"],
                "capacity": 4,
            },
            {
                "name": "Urban Loft Downtown",
                "description": "Modern loft in the city center.",
                "location": "New York, NY",
                "price_per_night": 200.00,
                "amenities": ["Gym", "Rooftop"],
                "capacity": 2,
            },
            {
                "name": "Mountain Retreat",
                "description": "Secluded cabin in the mountains.",
                "location": "Aspen, CO",
                "price_per_night": 180.00,
                "amenities": ["Fireplace", "Hiking Trails"],
                "capacity": 6,
            },
        ]

        # Seed listings
        for listing_data in sample_listings:
            try:
                listing, created = Listing.objects.get_or_create(
                    property_id=uuid.uuid4(),
                    host=host,
                    defaults={
                        "name": listing_data["name"],
                        "description": listing_data["description"],
                        "location": listing_data["location"],
                        "price_per_night": listing_data["price_per_night"],
                        "amenities": json.dumps(listing_data["amenities"]),
                        "capacity": listing_data["capacity"],
                    },
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created listing: {listing.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Listing already exists: {listing.name}")
                    )
            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating listing {listing_data["name"]}: {e}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Unexpected Error creating listing {listing_data["name"]}: {e}'
                    )
                )

        self.stdout.write(self.style.SUCCESS("Database seeding completed."))
