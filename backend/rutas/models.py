from django.core.exceptions import ValidationError
from django.db import models


class Parada(models.Model):
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"


class Ruta(models.Model):
    nombre = models.CharField(max_length=150)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class RutaParada(models.Model):
    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.CASCADE,
        related_name="paradas_ruta",
    )
    parada = models.ForeignKey(
        Parada,
        on_delete=models.PROTECT,
        related_name="rutas_parada",
    )
    orden = models.PositiveSmallIntegerField()
    minutos_desde_origen = models.PositiveIntegerField()

    class Meta:
        ordering = ("ruta", "orden")
        constraints = [
            models.UniqueConstraint(
                fields=("ruta", "orden"),
                name="rutas_rutaparada_ruta_orden_unico",
            ),
            models.UniqueConstraint(
                fields=("ruta", "parada"),
                name="rutas_rutaparada_ruta_parada_unica",
            ),
        ]

    def __str__(self):
        return f"{self.ruta} | {self.orden}: {self.parada}"


class Tarifa(models.Model):
    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.CASCADE,
        related_name="tarifas",
    )
    origen = models.ForeignKey(
        RutaParada,
        on_delete=models.PROTECT,
        related_name="tarifas_como_origen",
    )
    destino = models.ForeignKey(
        RutaParada,
        on_delete=models.PROTECT,
        related_name="tarifas_como_destino",
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ruta", "origen", "destino"),
                name="rutas_tarifa_tramo_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gt=0),
                name="rutas_tarifa_precio_mayor_cero",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.ruta_id and self.origen_id:
            if self.origen.ruta_id != self.ruta_id:
                errors["origen"] = "El origen debe pertenecer a la ruta."

        if self.ruta_id and self.destino_id:
            if self.destino.ruta_id != self.ruta_id:
                errors["destino"] = "El destino debe pertenecer a la ruta."

        if self.origen_id and self.destino_id:
            if self.origen_id == self.destino_id:
                errors["destino"] = "El origen y el destino deben ser distintos."
            elif self.origen.orden >= self.destino.orden:
                errors["destino"] = "El origen debe ser anterior al destino."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.ruta}: {self.origen.parada} → {self.destino.parada}"
