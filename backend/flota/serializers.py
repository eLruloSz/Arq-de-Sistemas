from config.api import ValidatedModelSerializer

from .models import Asiento, Bus


class BusSerializer(ValidatedModelSerializer):
    class Meta:
        model = Bus
        fields = (
            "id", "license_plate", "internal_number", "brand", "model",
            "active", "created_at",
        )
        read_only_fields = ("id", "created_at")
        extra_kwargs = {
            "license_plate": {"source": "patente"},
            "internal_number": {"source": "numero_interno"},
            "brand": {"source": "marca"},
            "model": {"source": "modelo"},
            "active": {"source": "activo"},
        }


class SeatSerializer(ValidatedModelSerializer):
    class Meta:
        model = Asiento
        fields = ("id", "bus", "number", "row", "column", "active")
        read_only_fields = ("id",)
        extra_kwargs = {
            "number": {"source": "numero"},
            "row": {"source": "fila"},
            "column": {"source": "columna"},
            "active": {"source": "activo"},
        }
