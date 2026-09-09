from django.test import TestCase
from django.utils import timezone

from flota.models import Bus
from rutas.models import Ruta

from .models import Viaje


class ViajeModelTests(TestCase):
    def setUp(self):
        self.ruta = Ruta.objects.create(nombre="Santiago - Arica")
        self.bus = Bus.objects.create(patente="ABCD12", numero_interno="12")

    def test_crear_viaje(self):
        salida = timezone.now()
        viaje = Viaje.objects.create(
            ruta=self.ruta,
            bus=self.bus,
            fecha_hora_salida=salida,
        )

        self.assertEqual(viaje.ruta, self.ruta)
        self.assertEqual(viaje.bus, self.bus)
        self.assertIn(self.ruta.nombre, str(viaje))

    def test_estado_por_defecto_es_programado(self):
        viaje = Viaje.objects.create(
            ruta=self.ruta,
            bus=self.bus,
            fecha_hora_salida=timezone.now(),
        )

        self.assertEqual(viaje.estado, Viaje.Estado.PROGRAMADO)

    def test_acepta_todos_los_estados_definidos(self):
        for estado in Viaje.Estado.values:
            with self.subTest(estado=estado):
                viaje = Viaje(
                    ruta=self.ruta,
                    bus=self.bus,
                    fecha_hora_salida=timezone.now(),
                    estado=estado,
                )
                viaje.full_clean()
