from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.api import AdministrativeViewSet, boolean_query, integer_query

from .models import Asiento, Bus
from .serializers import BusSerializer, SeatSerializer


class BusViewSet(AdministrativeViewSet):
    queryset = Bus.objects.order_by("pk")
    serializer_class = BusSerializer


class SeatViewSet(AdministrativeViewSet):
    queryset = Asiento.objects.select_related("bus").order_by("pk")
    serializer_class = SeatSerializer

    @extend_schema(parameters=[
        OpenApiParameter("bus", int, description="ID del bus."),
        OpenApiParameter("active", bool),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if "bus" in params:
            queryset = queryset.filter(bus_id=integer_query(params, "bus"))
        if "active" in params:
            queryset = queryset.filter(activo=boolean_query(params, "active"))
        return queryset
