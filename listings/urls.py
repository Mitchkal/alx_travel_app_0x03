from django.urls import path, include
from rest_framework import routers
from . import views

from listings.views import ListingViewSet, BookingViewSet, PaymentViewSet


router = routers.DefaultRouter()

router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    # path("", views.index, name="index"),
    # path("", views.)
    path("api/", include(router.urls)),
    path("api/health-check/", views.health_check, name="health_check"),
    path("api/payment/callback/", views.payment_callback, name="payment_callback"),
    # path("api/payment/callback/", views.payment_callback, name="payment_callback")
    # or any other view path
]
