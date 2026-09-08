from rest_framework import serializers

from config.api import ValidatedModelSerializer

from .models import Parada, Ruta, RutaParada, Tarifa


class StopSerializer(ValidatedModelSerializer):
    class Meta:
        model = Parada
        fields = ("id", "name", "city", "address", "active")
        read_only_fields = ("id",)
        extra_kwargs = {
            "name": {"source": "nombre"},
            "city": {"source": "ciudad"},
            "address": {"source": "direccion"},
            "active": {"source": "activo"},
        }


class RouteStopSerializer(serializers.ModelSerializer):
    route_stop_id = serializers.IntegerField(source="pk")
    stop_id = serializers.IntegerField(source="parada_id")
    name = serializers.CharField(source="parada.nombre")
    city = serializers.CharField(source="parada.ciudad")
    order = serializers.IntegerField(source="orden")
    minutes_from_origin = serializers.IntegerField(source="minutos_desde_origen")

    class Meta:
        model = RutaParada
        fields = (
            "route_stop_id", "stop_id", "name", "city",
            "order", "minutes_from_origin",
        )


class RouteSerializer(ValidatedModelSerializer):
    stops = RouteStopSerializer(
        source="paradas_ruta", many=True, read_only=True,
    )

    class Meta:
        model = Ruta
        fields = ("id", "name", "active", "created_at", "stops")
        read_only_fields = ("id", "created_at", "stops")
        extra_kwargs = {
            "name": {"source": "nombre"},
            "active": {"source": "activa"},
        }


class RouteStopInputSerializer(serializers.Serializer):
    stop_id = serializers.PrimaryKeyRelatedField(queryset=Parada.objects.all())
    order = serializers.IntegerField(min_value=0, max_value=32767)
    minutes_from_origin = serializers.IntegerField(
        min_value=0, max_value=2147483647,
    )


class RouteStopsInputSerializer(serializers.Serializer):
    stops = RouteStopInputSerializer(many=True, min_length=2)

    def validate_stops(self, stops):
        if len({item["stop_id"].pk for item in stops}) != len(stops):
            raise serializers.ValidationError("No repita paradas.")
        ordered = sorted(stops, key=lambda item: item["order"])
        if [item["order"] for item in ordered] != list(range(len(stops))):
            raise serializers.ValidationError(
                "Los órdenes deben ser consecutivos desde cero, sin repetir."
            )
        minutes = [item["minutes_from_origin"] for item in ordered]
        if minutes[0] != 0 or minutes != sorted(minutes):
            raise serializers.ValidationError(
                "Los minutos deben comenzar en cero y ser no decrecientes."
            )
        return ordered


class FareSerializer(ValidatedModelSerializer):
    class Meta:
        model = Tarifa
        fields = ("id", "route", "origin", "destination", "price", "active")
        read_only_fields = ("id",)
        extra_kwargs = {
            "route": {"source": "ruta"},
            "origin": {"source": "origen"},
            "destination": {"source": "destino"},
            "price": {"source": "precio"},
            "active": {"source": "activa"},
        }
