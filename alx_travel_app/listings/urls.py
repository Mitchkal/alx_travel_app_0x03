from django.urls import path, include
from rest_framework import routers
from . import views

from listings.views import ListingViewSet, BookingViewSet


router = routers.DefaultRouter()

router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = [
    # path("", views.index, name="index"),
    # path("", views.)
    path("api/", include(router.urls)),
    # or any other view path
]
