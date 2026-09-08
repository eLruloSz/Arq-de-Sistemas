from django.urls import include, path
from rest_framework.routers import SimpleRouter

from flota.views import BusViewSet, SeatViewSet
from rutas.views import (
    FareViewSet, RouteStopsView, RouteViewSet, StopViewSet,
)
from ventas.views import BookingViewSet
from viajes.views import TripAvailabilityView, TripSearchView, TripViewSet


router = SimpleRouter()
router.register("buses", BusViewSet)
router.register("seats", SeatViewSet)
router.register("stops", StopViewSet)
router.register("routes", RouteViewSet)
router.register("fares", FareViewSet)
router.register("trips", TripViewSet)
router.register("bookings", BookingViewSet)

urlpatterns = [
    path("trips/search/", TripSearchView.as_view(), name="trip-search"),
    path("trips/<int:pk>/availability/", TripAvailabilityView.as_view(),
         name="trip-availability"),
    path("routes/<int:pk>/stops/", RouteStopsView.as_view(), name="route-stops"),
    path("", include(router.urls)),
]
