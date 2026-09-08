import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from flota.models import Asiento
from rutas.models import RutaParada
from viajes.models import Viaje


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE_PAGO = "PENDIENTE_PAGO", "Pendiente de pago"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        CANCELADA = "CANCELADA", "Cancelada"

    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservas",
    )
    viaje = models.ForeignKey(
        Viaje,
        on_delete=models.PROTECT,
        related_name="reservas",
    )
    origen = models.ForeignKey(
        RutaParada,
        on_delete=models.PROTECT,
        related_name="reservas_como_origen",
    )
    destino = models.ForeignKey(
        RutaParada,
        on_delete=models.PROTECT,
        related_name="reservas_como_destino",
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE_PAGO,
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="ventas_reserva_total_no_negativo",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.viaje_id and self.origen_id:
            if self.origen.ruta_id != self.viaje.ruta_id:
                errors["origen"] = "El origen debe pertenecer a la ruta del viaje."

        if self.viaje_id and self.destino_id:
            if self.destino.ruta_id != self.viaje.ruta_id:
                errors["destino"] = "El destino debe pertenecer a la ruta del viaje."

        if self.origen_id and self.destino_id:
            if self.origen_id == self.destino_id:
                errors["destino"] = "El origen y el destino deben ser distintos."
            elif self.origen.orden >= self.destino.orden:
                errors["destino"] = "El origen debe ser anterior al destino."

        if self.total is not None and self.total < 0:
            errors["total"] = "El total no puede ser negativo."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Reserva {self.codigo}"


class Pasajero(models.Model):
    class TipoDocumento(models.TextChoices):
        RUT = "RUT", "RUT"
        PASAPORTE = "PASAPORTE", "Pasaporte"
        OTRO = "OTRO", "Otro"

    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name="pasajeros",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_documento = models.CharField(
        max_length=10,
        choices=TipoDocumento.choices,
    )
    documento = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.documento})"


class DetalleReserva(models.Model):
    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    pasajero = models.OneToOneField(
        Pasajero,
        on_delete=models.CASCADE,
        related_name="detalle",
    )
    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.PROTECT,
        related_name="detalles_reserva",
    )
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("reserva", "asiento"),
                name="ventas_detalle_reserva_asiento_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name="ventas_detalle_precio_no_negativo",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.reserva_id and self.pasajero_id:
            if self.pasajero.reserva_id != self.reserva_id:
                errors["pasajero"] = "El pasajero debe pertenecer a la reserva."

        if self.reserva_id and self.asiento_id:
            if self.asiento.bus_id != self.reserva.viaje.bus_id:
                errors["asiento"] = "El asiento debe pertenecer al bus del viaje."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.reserva} - {self.asiento}"


class Pago(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        ANULADO = "ANULADO", "Anulado"

    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.CASCADE,
        related_name="pago",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name="ventas_pago_monto_no_negativo",
            ),
        ]

    def __str__(self):
        return f"Pago de {self.reserva} - {self.get_estado_display()}"
