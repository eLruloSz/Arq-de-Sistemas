from rest_framework import serializers

from config.api import ValidatedModelSerializer
from rutas.models import Parada

from .models import Viaje


class TripSerializer(ValidatedModelSerializer):
    class Meta:
        model = Viaje
        fields = (
            "id", "route", "bus", "departure_datetime", "status", "created_at",
        )
        read_only_fields = ("id", "created_at")
        extra_kwargs = {
            "route": {"source": "ruta"},
            "departure_datetime": {"source": "fecha_hora_salida"},
            "status": {"source": "estado"},
        }


class SegmentQuerySerializer(serializers.Serializer):
    origin = serializers.PrimaryKeyRelatedField(
        queryset=Parada.objects.all(), help_text="Parada.id, no RutaParada.id.",
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Parada.objects.all(), help_text="Parada.id, no RutaParada.id.",
    )


class SearchQuerySerializer(SegmentQuerySerializer):
    date = serializers.DateField(
        input_formats=["%Y-%m-%d"],
        help_text="Fecha local (America/Santiago) de salida desde el origen.",
    )

    def validate(self, attrs):
        if attrs["origin"] == attrs["destination"]:
            raise serializers.ValidationError(
                "El origen y el destino deben ser distintos."
            )
        return attrs


class NamedResourceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class SearchResultSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField()
    route = NamedResourceSerializer()
    origin = NamedResourceSerializer()
    destination = NamedResourceSerializer()
    departure_datetime = serializers.DateTimeField()
    arrival_datetime = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_seats = serializers.IntegerField()


class AvailableSeatSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.CharField()
    row = serializers.IntegerField()
    column = serializers.IntegerField()
    available = serializers.BooleanField()


class AvailabilitySerializer(serializers.Serializer):
    trip_id = serializers.IntegerField()
    origin = NamedResourceSerializer()
    destination = NamedResourceSerializer()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    seats = AvailableSeatSerializer(many=True)
