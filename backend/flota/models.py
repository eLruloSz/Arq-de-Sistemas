from django.db import models


class Bus(models.Model):
    patente = models.CharField(max_length=10, unique=True)
    numero_interno = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50, blank=True)
    modelo = models.CharField(max_length=50, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "buses"

    def __str__(self):
        return f"Bus {self.numero_interno} - {self.patente}"


class Asiento(models.Model):
    bus = models.ForeignKey(
        Bus,
        on_delete=models.CASCADE,
        related_name="asientos",
    )
    numero = models.CharField(max_length=10)
    fila = models.PositiveSmallIntegerField()
    columna = models.PositiveSmallIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("bus", "numero"),
                name="flota_asiento_bus_numero_unico",
            ),
            models.UniqueConstraint(
                fields=("bus", "fila", "columna"),
                name="flota_asiento_bus_posicion_unica",
            ),
            models.CheckConstraint(
                condition=models.Q(fila__gt=0),
                name="flota_asiento_fila_mayor_cero",
            ),
            models.CheckConstraint(
                condition=models.Q(columna__gt=0),
                name="flota_asiento_columna_mayor_cero",
            ),
        ]

    def __str__(self):
        return f"Bus {self.bus.numero_interno} - Asiento {self.numero}"
