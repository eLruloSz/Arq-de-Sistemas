import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from flota.models import Asiento, Bus
from rutas.models import Parada, Ruta, RutaParada
from viajes.models import Viaje

from .models import DetalleReserva, Pago, Pasajero, Reserva


class VentasModelTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="pasajero",
            password="clave-segura",
        )
        self.bus = Bus.objects.create(patente="ABCD12", numero_interno="12")
        self.asiento = Asiento.objects.create(
            bus=self.bus,
            numero="1A",
            fila=1,
            columna=1,
        )
        self.otro_bus = Bus.objects.create(
            patente="EFGH34",
            numero_interno="13",
        )
        self.otro_asiento = Asiento.objects.create(
            bus=self.otro_bus,
            numero="1A",
            fila=1,
            columna=1,
        )
        self.ruta = Ruta.objects.create(nombre="Santiago - La Serena")
        parada_origen = Parada.objects.create(
            nombre="Terminal Santiago",
            ciudad="Santiago",
        )
        parada_destino = Parada.objects.create(
            nombre="Terminal La Serena",
            ciudad="La Serena",
        )
        self.origen = RutaParada.objects.create(
            ruta=self.ruta,
            parada=parada_origen,
            orden=0,
            minutos_desde_origen=0,
        )
        self.destino = RutaParada.objects.create(
            ruta=self.ruta,
            parada=parada_destino,
            orden=1,
            minutos_desde_origen=360,
        )
        self.viaje = Viaje.objects.create(
            ruta=self.ruta,
            bus=self.bus,
            fecha_hora_salida=timezone.now(),
        )
        self.reserva = self._crear_reserva()

    def _crear_reserva(self):
        return Reserva.objects.create(
            usuario=self.usuario,
            viaje=self.viaje,
            origen=self.origen,
            destino=self.destino,
            total=Decimal("15000.00"),
        )

    def _crear_pasajero(self, reserva=None, documento="11111111-1"):
        return Pasajero.objects.create(
            reserva=reserva or self.reserva,
            nombre="Ana",
            apellido="Pérez",
            tipo_documento=Pasajero.TipoDocumento.RUT,
            documento=documento,
        )

    def _crear_otra_ruta(self):
        ruta = Ruta.objects.create(nombre="Copiapó - Antofagasta")
        parada_origen = Parada.objects.create(
            nombre="Terminal Copiapó",
            ciudad="Copiapó",
        )
        parada_destino = Parada.objects.create(
            nombre="Terminal Antofagasta",
            ciudad="Antofagasta",
        )
        origen = RutaParada.objects.create(
            ruta=ruta,
            parada=parada_origen,
            orden=0,
            minutos_desde_origen=0,
        )
        destino = RutaParada.objects.create(
            ruta=ruta,
            parada=parada_destino,
            orden=1,
            minutos_desde_origen=300,
        )
        return origen, destino

    def test_crear_reserva_valida(self):
        self.reserva.full_clean()

        self.assertEqual(self.reserva.usuario, self.usuario)
        self.assertEqual(self.reserva.viaje, self.viaje)

    def test_estado_inicial_es_pendiente_pago(self):
        self.assertEqual(
            self.reserva.estado,
            Reserva.Estado.PENDIENTE_PAGO,
        )

    def test_codigo_uuid_es_generado(self):
        self.assertIsInstance(self.reserva.codigo, uuid.UUID)

    def test_reserva_rechaza_origen_de_otra_ruta(self):
        otro_origen, _ = self._crear_otra_ruta()
        reserva = Reserva(
            usuario=self.usuario,
            viaje=self.viaje,
            origen=otro_origen,
            destino=self.destino,
            total=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            reserva.full_clean()

    def test_reserva_rechaza_destino_de_otra_ruta(self):
        _, otro_destino = self._crear_otra_ruta()
        reserva = Reserva(
            usuario=self.usuario,
            viaje=self.viaje,
            origen=self.origen,
            destino=otro_destino,
            total=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            reserva.full_clean()

    def test_reserva_rechaza_origen_posterior_al_destino(self):
        reserva = Reserva(
            usuario=self.usuario,
            viaje=self.viaje,
            origen=self.destino,
            destino=self.origen,
            total=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            reserva.full_clean()

    def test_reserva_rechaza_origen_igual_al_destino(self):
        reserva = Reserva(
            usuario=self.usuario,
            viaje=self.viaje,
            origen=self.origen,
            destino=self.origen,
            total=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            reserva.full_clean()

    def test_reserva_rechaza_total_negativo(self):
        reserva = Reserva(
            usuario=self.usuario,
            viaje=self.viaje,
            origen=self.origen,
            destino=self.destino,
            total=Decimal("-1.00"),
        )

        with self.assertRaises(ValidationError):
            reserva.full_clean()

    def test_reserva_admite_multiples_pasajeros(self):
        self._crear_pasajero(documento="11111111-1")
        self._crear_pasajero(documento="22222222-2")

        self.assertEqual(self.reserva.pasajeros.count(), 2)

    def test_mismo_asiento_no_se_repite_en_una_reserva(self):
        pasajero_uno = self._crear_pasajero(documento="11111111-1")
        pasajero_dos = self._crear_pasajero(documento="22222222-2")
        DetalleReserva.objects.create(
            reserva=self.reserva,
            pasajero=pasajero_uno,
            asiento=self.asiento,
            precio_unitario=Decimal("15000.00"),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            DetalleReserva.objects.create(
                reserva=self.reserva,
                pasajero=pasajero_dos,
                asiento=self.asiento,
                precio_unitario=Decimal("15000.00"),
            )

    def test_mismo_asiento_se_permite_en_reservas_distintas(self):
        otra_reserva = self._crear_reserva()
        pasajero_uno = self._crear_pasajero(documento="11111111-1")
        pasajero_dos = self._crear_pasajero(
            reserva=otra_reserva,
            documento="22222222-2",
        )
        DetalleReserva.objects.create(
            reserva=self.reserva,
            pasajero=pasajero_uno,
            asiento=self.asiento,
            precio_unitario=Decimal("15000.00"),
        )

        detalle = DetalleReserva.objects.create(
            reserva=otra_reserva,
            pasajero=pasajero_dos,
            asiento=self.asiento,
            precio_unitario=Decimal("15000.00"),
        )

        self.assertEqual(detalle.asiento, self.asiento)

    def test_detalle_rechaza_asiento_de_otro_bus(self):
        pasajero = self._crear_pasajero()
        detalle = DetalleReserva(
            reserva=self.reserva,
            pasajero=pasajero,
            asiento=self.otro_asiento,
            precio_unitario=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            detalle.full_clean()

    def test_detalle_rechaza_pasajero_de_otra_reserva(self):
        otra_reserva = self._crear_reserva()
        pasajero = self._crear_pasajero(reserva=otra_reserva)
        detalle = DetalleReserva(
            reserva=self.reserva,
            pasajero=pasajero,
            asiento=self.asiento,
            precio_unitario=Decimal("15000.00"),
        )

        with self.assertRaises(ValidationError):
            detalle.full_clean()

    def test_detalle_rechaza_precio_unitario_negativo(self):
        pasajero = self._crear_pasajero()
        detalle = DetalleReserva(
            reserva=self.reserva,
            pasajero=pasajero,
            asiento=self.asiento,
            precio_unitario=Decimal("-1.00"),
        )

        with self.assertRaises(ValidationError):
            detalle.full_clean()

    def test_pago_es_unico_por_reserva(self):
        Pago.objects.create(reserva=self.reserva, monto=Decimal("15000.00"))

        with self.assertRaises(IntegrityError), transaction.atomic():
            Pago.objects.create(
                reserva=self.reserva,
                monto=Decimal("15000.00"),
            )

    def test_pago_rechaza_monto_negativo(self):
        pago = Pago(reserva=self.reserva, monto=Decimal("-1.00"))

        with self.assertRaises(ValidationError):
            pago.full_clean()

    def test_estado_inicial_del_pago_es_pendiente(self):
        pago = Pago.objects.create(
            reserva=self.reserva,
            monto=Decimal("15000.00"),
        )

        self.assertEqual(pago.estado, Pago.Estado.PENDIENTE)
