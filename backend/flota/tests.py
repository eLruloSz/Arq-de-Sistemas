from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Asiento, Bus


class BusModelTests(TestCase):
    def test_crear_bus(self):
        bus = Bus.objects.create(patente="ABCD12", numero_interno="12")

        self.assertEqual(str(bus), "Bus 12 - ABCD12")
        self.assertTrue(bus.activo)

    def test_patente_debe_ser_unica(self):
        Bus.objects.create(patente="ABCD12", numero_interno="12")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Bus.objects.create(patente="ABCD12", numero_interno="13")

    def test_numero_interno_debe_ser_unico(self):
        Bus.objects.create(patente="ABCD12", numero_interno="12")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Bus.objects.create(patente="EFGH34", numero_interno="12")


class AsientoModelTests(TestCase):
    def setUp(self):
        self.bus = Bus.objects.create(patente="ABCD12", numero_interno="12")

    def test_crear_asiento(self):
        asiento = Asiento.objects.create(
            bus=self.bus,
            numero="1A",
            fila=1,
            columna=1,
        )

        self.assertEqual(str(asiento), "Bus 12 - Asiento 1A")
        self.assertTrue(asiento.activo)

    def test_numero_debe_ser_unico_en_el_mismo_bus(self):
        Asiento.objects.create(bus=self.bus, numero="1A", fila=1, columna=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Asiento.objects.create(
                bus=self.bus,
                numero="1A",
                fila=1,
                columna=2,
            )

    def test_mismo_numero_se_permite_en_buses_distintos(self):
        otro_bus = Bus.objects.create(patente="EFGH34", numero_interno="13")
        Asiento.objects.create(bus=self.bus, numero="1A", fila=1, columna=1)

        asiento = Asiento.objects.create(
            bus=otro_bus,
            numero="1A",
            fila=1,
            columna=1,
        )

        self.assertEqual(asiento.numero, "1A")

    def test_posicion_debe_ser_unica_en_el_mismo_bus(self):
        Asiento.objects.create(bus=self.bus, numero="1A", fila=1, columna=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Asiento.objects.create(
                bus=self.bus,
                numero="1B",
                fila=1,
                columna=1,
            )

    def test_fila_y_columna_deben_ser_mayores_que_cero(self):
        for fila, columna in ((0, 1), (1, 0)):
            with self.subTest(fila=fila, columna=columna):
                asiento = Asiento(
                    bus=self.bus,
                    numero=f"{fila}-{columna}",
                    fila=fila,
                    columna=columna,
                )
                with self.assertRaises(ValidationError):
                    asiento.full_clean()
