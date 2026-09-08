from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import (
    AdministrativeViewSet, DomainErrorSerializer, boolean_query, integer_query,
)
from usuarios.permissions import IsAdministrator

from .models import Parada, Ruta, RutaParada, Tarifa
from .serializers import (
    FareSerializer, RouteSerializer, RouteStopSerializer,
    RouteStopsInputSerializer, StopSerializer,
)
from .services import RouteInUseError, replace_route_stops


class StopViewSet(AdministrativeViewSet):
    """GET público de paradas activas; POST/PATCH solo para administradores."""
    queryset = Parada.objects.order_by("pk")
    serializer_class = StopSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdministrator()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method in ("GET", "HEAD"):
            queryset = queryset.filter(activo=True)
        return queryset


class RouteViewSet(AdministrativeViewSet):
    queryset = Ruta.objects.prefetch_related(Prefetch(
        "paradas_ruta",
        queryset=RutaParada.objects.select_related("parada").order_by("orden"),
    )).order_by("pk")
    serializer_class = RouteSerializer


class FareViewSet(AdministrativeViewSet):
    queryset = Tarifa.objects.select_related(
        "ruta", "origen", "destino",
    ).order_by("pk")
    serializer_class = FareSerializer

    @extend_schema(parameters=[
        OpenApiParameter("route", int),
        OpenApiParameter("active", bool),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if "route" in params:
            queryset = queryset.filter(ruta_id=integer_query(params, "route"))
        if "active" in params:
            queryset = queryset.filter(activa=boolean_query(params, "active"))
        return queryset


class RouteStopsView(APIView):
    permission_classes = (IsAdministrator,)

    @extend_schema(responses=RouteStopSerializer(many=True))
    def get(self, request, pk):
        route = get_object_or_404(Ruta, pk=pk)
        stops = route.paradas_ruta.select_related("parada").order_by("orden")
        return Response(RouteStopSerializer(stops, many=True).data)

    @extend_schema(
        request=RouteStopsInputSerializer,
        responses={200: RouteStopSerializer(many=True),
                   409: DomainErrorSerializer},
        description=(
            "Reemplazo completo atómico. Órdenes consecutivos desde 0, "
            "minutos no decrecientes desde 0. Una ruta con viajes o tarifas "
            "devuelve 409 ROUTE_IN_USE y conserva sus paradas."
        ),
    )
    def put(self, request, pk):
        route = get_object_or_404(Ruta, pk=pk)
        serializer = RouteStopsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            replace_route_stops(
                route=route, stops=serializer.validated_data["stops"],
            )
        except RouteInUseError as exc:
            return Response(
                {"code": "ROUTE_IN_USE", "message": str(exc), "details": {}},
                status=409,
            )
        return self.get(request, pk)
