from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import AdministrativeViewSet, DOMAIN_RESPONSES
from ventas.services import _get_active_fare, get_available_seats

from .models import Viaje
from .serializers import (
    AvailabilitySerializer, SearchQuerySerializer, SearchResultSerializer,
    SegmentQuerySerializer, TripSerializer,
)
from .services import resolve_segment, search_trips


class TripViewSet(AdministrativeViewSet):
    queryset = Viaje.objects.select_related("ruta", "bus").order_by("pk")
    serializer_class = TripSerializer


class TripSearchView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[SearchQuerySerializer],
        responses={200: SearchResultSerializer(many=True), **DOMAIN_RESPONSES},
        description=(
            "Búsqueda pública por Parada.id y fecha local de salida en origen. "
            "Incluye viajes que comenzaron el día anterior. Parámetros "
            "ausentes, fechas inválidas y paradas inexistentes devuelven 400."
        ),
    )
    def get(self, request):
        query = SearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        results = search_trips(**query.validated_data)
        return Response(SearchResultSerializer(results, many=True).data)


class TripAvailabilityView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[SegmentQuerySerializer],
        responses={200: AvailabilitySerializer, **DOMAIN_RESPONSES},
        description=(
            "Mapa de asientos activos para un tramo (Parada.id). "
            "No garantiza la reserva: la creación vuelve a validar."
        ),
    )
    def get(self, request, pk):
        trip = get_object_or_404(
            Viaje.objects.select_related("ruta", "bus"), pk=pk,
        )
        query = SegmentQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        origin = query.validated_data["origin"]
        destination = query.validated_data["destination"]
        route_origin, route_destination = resolve_segment(
            viaje=trip, origin=origin, destination=destination,
        )
        available_ids = set(get_available_seats(
            viaje=trip, origen=route_origin, destino=route_destination,
        ).values_list("pk", flat=True))
        fare = _get_active_fare(
            viaje=trip, origen=route_origin, destino=route_destination,
        )
        seats = trip.bus.asientos.filter(activo=True).order_by(
            "fila", "columna", "pk",
        )
        result = {
            "trip_id": trip.pk,
            "origin": {"id": origin.pk, "name": origin.nombre},
            "destination": {"id": destination.pk, "name": destination.nombre},
            "price": fare.precio,
            "seats": [
                {"id": seat.pk, "number": seat.numero, "row": seat.fila,
                 "column": seat.columna, "available": seat.pk in available_ids}
                for seat in seats
            ],
        }
        return Response(AvailabilitySerializer(result).data)
