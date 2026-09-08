from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Parada, Ruta, RutaParada, Tarifa


class RutasModelTests(TestCase):
    def setUp(self):
        self.parada_origen = Parada.objects.create(
            nombre="Terminal Santiago",
            ciudad="Santiago",
        )
        self.parada_destino = Parada.objects.create(
            nombre="Terminal La Serena",
            ciudad="La Serena",
        )
        self.ruta = Ruta.objects.create(nombre="Santiago - La Serena")
        self.origen = RutaParada.objects.create(
            ruta=self.ruta,
            parada=self.parada_origen,
            orden=0,
            minutos_desde_origen=0,
        )
        self.destino = RutaParada.objects.create(
            ruta=self.ruta,
            parada=self.parada_destino,
            orden=1,
            minutos_desde_origen=360,
        )

    def test_crear_parada(self):
        parada = Parada.objects.create(nombre="Terminal", ciudad="Copiapó")

        self.assertEqual(str(parada), "Terminal - Copiapó")
        self.assertTrue(parada.activo)

    def test_crear_ruta(self):
        ruta = Ruta.objects.create(nombre="Copiapó - Antofagasta")

        self.assertEqual(str(ruta), "Copiapó - Antofagasta")
        self.assertTrue(ruta.activa)

    def test_crear_ruta_parada_permite_orden_cero(self):
        self.assertEqual(self.origen.orden, 0)
        self.assertEqual(self.ruta.paradas_ruta.first(), self.origen)

    def test_orden_debe_ser_unico_en_la_ruta(self):
        otra_parada = Parada.objects.create(nombre="Terminal Norte", ciudad="Coquimbo")

        with self.assertRaises(IntegrityError), transaction.atomic():
            RutaParada.objects.create(
                ruta=self.ruta,
                parada=otra_parada,
                orden=1,
                minutos_desde_origen=300,
            )

    def test_parada_debe_ser_unica_en_la_ruta(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RutaParada.objects.create(
                ruta=self.ruta,
                parada=self.parada_destino,
                orden=2,
                minutos_desde_origen=400,
            )

    def test_tarifa_valida(self):
        tarifa = Tarifa(
            ruta=self.ruta,
            origen=self.origen,
            destino=self.destino,
            precio=Decimal("15000.00"),
        )

        tarifa.full_clean()
        tarifa.save()

        self.assertEqual(self.ruta.tarifas.get(), tarifa)

    def test_tarifa_rechaza_origen_posterior_al_destino(self):
        tarifa = Tarifa(
            ruta=self.ruta,
            origen=self.destino,
            destino=self.origen,
            precio=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            tarifa.full_clean()

    def test_tarifa_rechaza_origen_igual_al_destino(self):
        tarifa = Tarifa(
            ruta=self.ruta,
            origen=self.origen,
            destino=self.origen,
            precio=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            tarifa.full_clean()

    def test_tarifa_rechaza_paradas_de_otra_ruta(self):
        otra_ruta = Ruta.objects.create(nombre="Copiapó - Arica")
        otra_parada = Parada.objects.create(nombre="Terminal Copiapó", ciudad="Copiapó")
        otro_origen = RutaParada.objects.create(
            ruta=otra_ruta,
            parada=otra_parada,
            orden=0,
            minutos_desde_origen=0,
        )
        tarifa = Tarifa(
            ruta=self.ruta,
            origen=otro_origen,
            destino=self.destino,
            precio=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            tarifa.full_clean()

    def test_tarifa_debe_ser_unica_por_tramo(self):
        Tarifa.objects.create(
            ruta=self.ruta,
            origen=self.origen,
            destino=self.destino,
            precio=Decimal("15000.00"),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Tarifa.objects.create(
                ruta=self.ruta,
                origen=self.origen,
                destino=self.destino,
                precio=Decimal("20000.00"),
            )

    def test_tarifa_rechaza_precio_no_positivo(self):
        for precio in (Decimal("0.00"), Decimal("-1.00")):
            with self.subTest(precio=precio):
                tarifa = Tarifa(
                    ruta=self.ruta,
                    origen=self.origen,
                    destino=self.destino,
                    precio=precio,
                )
                with self.assertRaises(ValidationError):
                    tarifa.full_clean()
