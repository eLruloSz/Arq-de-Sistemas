from django.db import models

from flota.models import Bus
from rutas.models import Ruta


class Viaje(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADO = "PROGRAMADO", "Programado"
        EN_CURSO = "EN_CURSO", "En curso"
        FINALIZADO = "FINALIZADO", "Finalizado"
        CANCELADO = "CANCELADO", "Cancelado"

    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.PROTECT,
        related_name="viajes",
    )
    bus = models.ForeignKey(
        Bus,
        on_delete=models.PROTECT,
        related_name="viajes",
    )
    fecha_hora_salida = models.DateTimeField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADO,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        salida = self.fecha_hora_salida.strftime("%d/%m/%Y %H:%M")
        return f"{self.ruta} | {salida}"
