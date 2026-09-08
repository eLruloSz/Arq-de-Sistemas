from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.api import DOMAIN_RESPONSES, DomainErrorSerializer
from viajes.models import Viaje
from viajes.services import resolve_segment

from .models import DetalleReserva, Reserva
from .serializers import (
    BookingActionInputSerializer, BookingInputSerializer, BookingSerializer,
)
from .services import cancel_reservation, create_reservation, pay_reservation


LIFECYCLE_RESPONSES = {
    200: BookingSerializer,
    400: OpenApiResponse(description="Card or external payment data rejected."),
    401: OpenApiResponse(description="Authentication required."),
    404: OpenApiResponse(description="Booking not found or not owned by this user."),
    409: OpenApiResponse(
        DomainErrorSerializer,
        description="Invalid booking transition or inconsistent payment.",
    ),
}


class BookingViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingSerializer
    http_method_names = ("get", "post", "head", "options")
    queryset = Reserva.objects.select_related(
        "viaje", "origen__parada", "destino__parada", "pago",
    ).prefetch_related(Prefetch(
        "detalles",
        queryset=DetalleReserva.objects.select_related(
            "pasajero", "asiento",
        ).order_by("pk"),
    )).order_by("-created_at", "-pk")

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if not self.request.user.is_staff:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset

    def _transition(self, request, service):
        reservation = self.get_object()
        serializer = BookingActionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service(reservation_id=reservation.pk)
        reservation = self.get_queryset().get(pk=reservation.pk)
        return Response(self.get_serializer(reservation).data)

    @extend_schema(
        request=None, responses=LIFECYCLE_RESPONSES,
        description=(
            "Simulated payment using the booking total; no request body needed. "
            "Amount fields are ignored. Card and external payment data are rejected. "
            "Owner or administrator only. Conflicts: BOOKING_NOT_PAYABLE."
        ),
    )
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        return self._transition(request, pay_reservation)

    @extend_schema(
        request=None, responses=LIFECYCLE_RESPONSES,
        description=(
            "Cancel a pending or confirmed booking; void its simulated payment "
            "if approved. No request body needed. Owner or administrator only. "
            "Conflicts: BOOKING_NOT_CANCELLABLE, including inconsistent payments."
        ),
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, cancel_reservation)

    @extend_schema(
        request=BookingInputSerializer,
        responses={201: BookingSerializer, **DOMAIN_RESPONSES},
        description=(
            "Crea mediante el servicio atómico. Propietario=request.user. "
            "Se ignoran campos externos de usuario, precio, total y estado. "
            "origin_id y destination_id son Parada.id. No crea pagos."
        ),
    )
    def create(self, request):
        serializer = BookingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        trip = get_object_or_404(
            Viaje.objects.select_related("ruta"), pk=data["trip_id"],
        )
        origin, destination = resolve_segment(
            viaje=trip, origin=data["origin_id"],
            destination=data["destination_id"],
        )
        passengers = [
            {
                "asiento_id": passenger["seat_id"],
                "nombre": passenger["first_name"],
                "apellido": passenger["last_name"],
                "tipo_documento": passenger["document_type"],
                "documento": passenger["document_number"],
            }
            for passenger in data["passengers"]
        ]
        reservation = create_reservation(
            usuario=request.user, viaje=trip, origen=origin,
            destino=destination, pasajeros=passengers,
        )
        reservation = self.get_queryset().get(pk=reservation.pk)
        return Response(BookingSerializer(reservation).data, status=201)
