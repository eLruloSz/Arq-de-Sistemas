from rest_framework import serializers

from rutas.models import Parada
from viajes.serializers import NamedResourceSerializer

from .models import DetalleReserva, Pago, Pasajero, Reserva


class BookingActionInputSerializer(serializers.Serializer):
    """Sin campos de entrada: ignora montos, rechaza datos de pago real."""

    def to_internal_value(self, data):
        forbidden = {
            "card_number", "cvv", "expiration", "holder", "gateway",
            "transaction_id",
        }
        if isinstance(data, dict) and forbidden.intersection(data):
            raise serializers.ValidationError(
                {"non_field_errors": [
                    "Card and external payment data are not accepted.",
                ]}
            )
        return super().to_internal_value(data)


class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(source="monto", max_digits=12, decimal_places=2)
    status = serializers.CharField(source="estado")

    class Meta:
        model = Pago
        fields = ("id", "amount", "status", "paid_at")
        read_only_fields = fields


class BookingPassengerInputSerializer(serializers.Serializer):
    seat_id = serializers.IntegerField(min_value=1, max_value=9223372036854775807)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    document_type = serializers.ChoiceField(choices=Pasajero.TipoDocumento.choices)
    document_number = serializers.CharField(max_length=30)


class BookingInputSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField(min_value=1, max_value=9223372036854775807)
    origin_id = serializers.PrimaryKeyRelatedField(
        queryset=Parada.objects.all(), help_text="Parada.id.",
    )
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Parada.objects.all(), help_text="Parada.id.",
    )
    passengers = BookingPassengerInputSerializer(many=True, min_length=1)


class BookingSeatSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.CharField(source="numero")


class BookingPassengerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pasajero_id")
    first_name = serializers.CharField(source="pasajero.nombre")
    last_name = serializers.CharField(source="pasajero.apellido")
    document_type = serializers.CharField(source="pasajero.tipo_documento")
    document_number = serializers.CharField(source="pasajero.documento")
    seat = BookingSeatSerializer(source="asiento")
    price = serializers.DecimalField(
        source="precio_unitario", max_digits=10, decimal_places=2,
    )

    class Meta:
        model = DetalleReserva
        fields = (
            "id", "first_name", "last_name", "document_type",
            "document_number", "seat", "price",
        )


class BookingTripSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class BookingStopSerializer(NamedResourceSerializer):
    name = serializers.CharField(source="nombre")


class BookingSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(source="pago", read_only=True, allow_null=True)
    code = serializers.UUIDField(source="codigo")
    status = serializers.CharField(source="estado")
    trip = BookingTripSerializer(source="viaje")
    origin = BookingStopSerializer(source="origen.parada")
    destination = BookingStopSerializer(source="destino.parada")
    passengers = BookingPassengerSerializer(source="detalles", many=True)

    class Meta:
        model = Reserva
        fields = (
            "id", "code", "status", "trip", "origin", "destination",
            "passengers", "total", "created_at", "payment",
        )
        read_only_fields = fields
