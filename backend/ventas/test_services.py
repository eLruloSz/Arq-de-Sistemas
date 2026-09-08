from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from flota.models import Asiento, Bus
from rutas.models import Parada, Ruta, RutaParada, Tarifa
from viajes.models import Viaje

from .exceptions import (
    FareNotFoundError,
    InvalidReservationError,
    InvalidSeatError,
    InvalidSegmentError,
    SeatUnavailableError,
    TripNotAvailableError,
)
from .models import DetalleReserva, Pasajero, Reserva
from .services import (
    create_reservation,
    get_available_seats,
    get_unavailable_seat_ids,
    validate_segment,
)


class ReservationServiceFixtures:
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="usuario-a")
        self.other_user = get_user_model().objects.create_user(
            username="usuario-b"
        )
        self.bus = Bus.objects.create(
            patente="ABCD12",
            numero_interno="12",
        )
        self.seat_1a = Asiento.objects.create(
            bus=self.bus,
            numero="1A",
            fila=1,
            columna=1,
        )
        self.seat_1b = Asiento.objects.create(
            bus=self.bus,
            numero="1B",
            fila=1,
            columna=2,
        )
        self.inactive_seat = Asiento.objects.create(
            bus=self.bus,
            numero="2A",
            fila=2,
            columna=1,
            activo=False,
        )
        self.other_bus = Bus.objects.create(
            patente="EFGH34",
            numero_interno="13",
        )
        self.other_bus_seat = Asiento.objects.create(
            bus=self.other_bus,
            numero="1A",
            fila=1,
            columna=1,
        )
        self.route = Ruta.objects.create(nombre="Santiago - Arica")
        stop_data = (
            ("Santiago", 0),
            ("La Serena", 360),
            ("Copiapó", 660),
            ("Antofagasta", 960),
            ("Arica", 1260),
        )
        self.route_stops = []
        for order, (city, minutes) in enumerate(stop_data):
            stop = Parada.objects.create(
                nombre=f"Terminal {city}",
                ciudad=city,
            )
            self.route_stops.append(
                RutaParada.objects.create(
                    ruta=self.route,
                    parada=stop,
                    orden=order,
                    minutos_desde_origen=minutes,
                )
            )

        self.trip = Viaje.objects.create(
            ruta=self.route,
            bus=self.bus,
            fecha_hora_salida=timezone.now(),
        )
        self.other_trip = Viaje.objects.create(
            ruta=self.route,
            bus=self.bus,
            fecha_hora_salida=timezone.now(),
        )
        self.fare = Tarifa.objects.create(
            ruta=self.route,
            origen=self.route_stops[1],
            destino=self.route_stops[3],
            precio=Decimal("30000.00"),
        )

    def passenger_request(
        self,
        *,
        seat=None,
        name="Juan",
        document="11111111-1",
    ):
        return {
            "asiento_id": (seat or self.seat_1a).pk,
            "nombre": name,
            "apellido": "Pérez",
            "tipo_documento": Pasajero.TipoDocumento.RUT,
            "documento": document,
        }

    def create_existing_reservation(
        self,
        *,
        seat=None,
        trip=None,
        state=Reserva.Estado.PENDIENTE_PAGO,
        origin=None,
        destination=None,
    ):
        reservation = Reserva.objects.create(
            usuario=self.user,
            viaje=trip or self.trip,
            origen=origin or self.route_stops[1],
            destino=destination or self.route_stops[3],
            estado=state,
            total=self.fare.precio,
        )
        passenger = Pasajero.objects.create(
            reserva=reservation,
            nombre="Existente",
            apellido="Pasajero",
            tipo_documento=Pasajero.TipoDocumento.RUT,
            documento=f"DOC-{reservation.pk}",
        )
        DetalleReserva.objects.create(
            reserva=reservation,
            pasajero=passenger,
            asiento=seat or self.seat_1a,
            precio_unitario=self.fare.precio,
        )
        return reservation


class SegmentValidationTests(ReservationServiceFixtures, TestCase):
    def test_accepts_valid_segment(self):
        validate_segment(
            viaje=self.trip,
            origen=self.route_stops[1],
            destino=self.route_stops[3],
        )

    def test_rejects_origin_from_another_route(self):
        other_origin, _ = self._create_other_route_stops()

        with self.assertRaises(InvalidSegmentError):
            validate_segment(
                viaje=self.trip,
                origen=other_origin,
                destino=self.route_stops[3],
            )

    def test_rejects_destination_from_another_route(self):
        _, other_destination = self._create_other_route_stops()

        with self.assertRaises(InvalidSegmentError):
            validate_segment(
                viaje=self.trip,
                origen=self.route_stops[1],
                destino=other_destination,
            )

    def test_rejects_equal_origin_and_destination(self):
        with self.assertRaises(InvalidSegmentError):
            validate_segment(
                viaje=self.trip,
                origen=self.route_stops[1],
                destino=self.route_stops[1],
            )

    def test_rejects_origin_after_destination(self):
        with self.assertRaises(InvalidSegmentError):
            validate_segment(
                viaje=self.trip,
                origen=self.route_stops[3],
                destino=self.route_stops[1],
            )

    def _create_other_route_stops(self):
        route = Ruta.objects.create(nombre="Valparaíso - Temuco")
        origin_stop = Parada.objects.create(
            nombre="Terminal Valparaíso",
            ciudad="Valparaíso",
        )
        destination_stop = Parada.objects.create(
            nombre="Terminal Temuco",
            ciudad="Temuco",
        )
        origin = RutaParada.objects.create(
            ruta=route,
            parada=origin_stop,
            orden=0,
            minutos_desde_origen=0,
        )
        destination = RutaParada.objects.create(
            ruta=route,
            parada=destination_stop,
            orden=1,
            minutos_desde_origen=500,
        )
        return origin, destination


class SeatAvailabilityTests(ReservationServiceFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.create_existing_reservation()

    def assert_seat_available(self, origin_order, destination_order):
        seats = get_available_seats(
            viaje=self.trip,
            origen=self.route_stops[origin_order],
            destino=self.route_stops[destination_order],
        )
        self.assertIn(self.seat_1a, seats)

    def assert_seat_unavailable(self, origin_order, destination_order):
        unavailable_ids = get_unavailable_seat_ids(
            viaje=self.trip,
            origen=self.route_stops[origin_order],
            destino=self.route_stops[destination_order],
        )
        self.assertIn(self.seat_1a.pk, unavailable_ids)
        seats = get_available_seats(
            viaje=self.trip,
            origen=self.route_stops[origin_order],
            destino=self.route_stops[destination_order],
        )
        self.assertNotIn(self.seat_1a, seats)

    def test_previous_adjacent_segment_is_available(self):
        self.assert_seat_available(0, 1)

    def test_next_adjacent_segment_is_available(self):
        self.assert_seat_available(3, 4)

    def test_left_overlap_is_unavailable(self):
        self.assert_seat_unavailable(0, 2)

    def test_right_overlap_is_unavailable(self):
        self.assert_seat_unavailable(2, 4)

    def test_identical_segment_is_unavailable(self):
        self.assert_seat_unavailable(1, 3)

    def test_contained_segment_is_unavailable(self):
        self.assert_seat_unavailable(2, 3)

    def test_containing_segment_is_unavailable(self):
        self.assert_seat_unavailable(0, 4)

    def test_same_seat_on_another_trip_is_available(self):
        seats = get_available_seats(
            viaje=self.other_trip,
            origen=self.route_stops[1],
            destino=self.route_stops[3],
        )

        self.assertIn(self.seat_1a, seats)

    def test_another_seat_on_same_trip_is_available(self):
        seats = get_available_seats(
            viaje=self.trip,
            origen=self.route_stops[1],
            destino=self.route_stops[3],
        )

        self.assertIn(self.seat_1b, seats)

    def test_pending_reservation_blocks_seat(self):
        self.assert_seat_unavailable(1, 3)

    def test_confirmed_reservation_blocks_seat(self):
        Reserva.objects.update(estado=Reserva.Estado.CONFIRMADA)

        self.assert_seat_unavailable(1, 3)

    def test_cancelled_reservation_does_not_block_seat(self):
        Reserva.objects.update(estado=Reserva.Estado.CANCELADA)

        self.assert_seat_available(1, 3)

    def test_inactive_seat_is_not_returned(self):
        seats = get_available_seats(
            viaje=self.trip,
            origen=self.route_stops[0],
            destino=self.route_stops[1],
        )

        self.assertNotIn(self.inactive_seat, seats)

    def test_non_programmed_trip_rejects_availability_query(self):
        self.trip.estado = Viaje.Estado.CANCELADO
        self.trip.save(update_fields=("estado",))

        with self.assertRaises(TripNotAvailableError):
            get_available_seats(
                viaje=self.trip,
                origen=self.route_stops[1],
                destino=self.route_stops[3],
            )


class ReservationCreationTests(ReservationServiceFixtures, TestCase):
    def create_service_reservation(self, *, passengers=None, **kwargs):
        return create_reservation(
            usuario=kwargs.get("usuario", self.user),
            viaje=kwargs.get("viaje", self.trip),
            origen=kwargs.get("origen", self.route_stops[1]),
            destino=kwargs.get("destino", self.route_stops[3]),
            pasajeros=passengers or [self.passenger_request()],
        )

    def test_programmed_trip_accepts_reservation(self):
        reservation = self.create_service_reservation()

        self.assertEqual(reservation.viaje, self.trip)

    def test_cancelled_trip_rejects_reservation(self):
        self._assert_trip_state_rejected(Viaje.Estado.CANCELADO)

    def test_in_progress_trip_rejects_reservation(self):
        self._assert_trip_state_rejected(Viaje.Estado.EN_CURSO)

    def test_finished_trip_rejects_reservation(self):
        self._assert_trip_state_rejected(Viaje.Estado.FINALIZADO)

    def test_active_fare_is_used(self):
        reservation = self.create_service_reservation()

        self.assertEqual(reservation.total, self.fare.precio)

    def test_missing_fare_is_rejected(self):
        self.fare.delete()

        with self.assertRaises(FareNotFoundError):
            self.create_service_reservation()

    def test_inactive_fare_is_rejected(self):
        self.fare.activa = False
        self.fare.save(update_fields=("activa",))

        with self.assertRaises(FareNotFoundError):
            self.create_service_reservation()

    def test_valid_seat_is_accepted(self):
        reservation = self.create_service_reservation()

        self.assertEqual(reservation.detalles.get().asiento, self.seat_1a)

    def test_inactive_seat_is_rejected(self):
        request = self.passenger_request(seat=self.inactive_seat)

        with self.assertRaises(InvalidSeatError):
            self.create_service_reservation(passengers=[request])

    def test_seat_from_another_bus_is_rejected(self):
        request = self.passenger_request(seat=self.other_bus_seat)

        with self.assertRaises(InvalidSeatError):
            self.create_service_reservation(passengers=[request])

    def test_nonexistent_seat_is_rejected(self):
        request = self.passenger_request()
        request["asiento_id"] = 999999

        with self.assertRaises(InvalidSeatError):
            self.create_service_reservation(passengers=[request])

    def test_duplicate_seat_in_request_is_rejected(self):
        first = self.passenger_request()
        second = self.passenger_request(
            name="María",
            document="22222222-2",
        )

        with self.assertRaises(InvalidSeatError):
            self.create_service_reservation(passengers=[first, second])

    def test_empty_passenger_list_is_rejected(self):
        with self.assertRaises(InvalidReservationError):
            create_reservation(
                usuario=self.user,
                viaje=self.trip,
                origen=self.route_stops[1],
                destino=self.route_stops[3],
                pasajeros=[],
            )

    def test_creates_one_passenger_and_detail(self):
        reservation = self.create_service_reservation()

        self.assertEqual(reservation.pasajeros.count(), 1)
        self.assertEqual(reservation.detalles.count(), 1)

    def test_creates_multiple_passengers_and_details(self):
        passengers = [
            self.passenger_request(),
            self.passenger_request(
                seat=self.seat_1b,
                name="María",
                document="22222222-2",
            ),
        ]

        reservation = self.create_service_reservation(passengers=passengers)

        self.assertEqual(reservation.pasajeros.count(), 2)
        self.assertEqual(reservation.detalles.count(), 2)

    def test_initial_state_is_pending_payment(self):
        reservation = self.create_service_reservation()

        self.assertEqual(
            reservation.estado,
            Reserva.Estado.PENDIENTE_PAGO,
        )

    def test_total_is_calculated_from_fare_and_passenger_count(self):
        passengers = [
            self.passenger_request(),
            self.passenger_request(
                seat=self.seat_1b,
                name="María",
                document="22222222-2",
            ),
        ]

        reservation = self.create_service_reservation(passengers=passengers)

        self.assertEqual(reservation.total, Decimal("60000.00"))

    def test_unit_price_is_persisted_from_fare(self):
        reservation = self.create_service_reservation()

        self.assertEqual(
            reservation.detalles.get().precio_unitario,
            Decimal("30000.00"),
        )

    def test_passenger_data_is_associated_correctly(self):
        reservation = self.create_service_reservation()
        passenger = reservation.pasajeros.get()

        self.assertEqual(passenger.nombre, "Juan")
        self.assertEqual(passenger.documento, "11111111-1")
        self.assertEqual(passenger.detalle.asiento, self.seat_1a)

    def test_occupied_seat_is_rejected(self):
        self.create_existing_reservation()

        with self.assertRaises(SeatUnavailableError) as context:
            self.create_service_reservation()

        self.assertEqual(context.exception.seat_ids, (self.seat_1a.pk,))

    def test_request_rolls_back_completely_when_one_seat_is_occupied(self):
        self.create_existing_reservation(seat=self.seat_1b)
        counts_before = (
            Reserva.objects.count(),
            Pasajero.objects.count(),
            DetalleReserva.objects.count(),
        )
        passengers = [
            self.passenger_request(),
            self.passenger_request(
                seat=self.seat_1b,
                name="María",
                document="22222222-2",
            ),
        ]

        with self.assertRaises(SeatUnavailableError):
            self.create_service_reservation(passengers=passengers)

        self.assertEqual(
            (
                Reserva.objects.count(),
                Pasajero.objects.count(),
                DetalleReserva.objects.count(),
            ),
            counts_before,
        )

    def _assert_trip_state_rejected(self, state):
        self.trip.estado = state
        self.trip.save(update_fields=("estado",))

        with self.assertRaises(TripNotAvailableError):
            self.create_service_reservation()


class ReservationConcurrencyTests(
    ReservationServiceFixtures,
    TransactionTestCase,
):
    def test_concurrent_requests_create_exactly_one_reservation(self):
        barrier = Barrier(2)

        def attempt_reservation(user_id):
            close_old_connections()
            try:
                user = get_user_model().objects.get(pk=user_id)
                trip = Viaje.objects.get(pk=self.trip.pk)
                origin = RutaParada.objects.get(pk=self.route_stops[1].pk)
                destination = RutaParada.objects.get(pk=self.route_stops[3].pk)
                seat = Asiento.objects.get(pk=self.seat_1a.pk)
                request = self.passenger_request(
                    seat=seat,
                    document=f"DOC-{user_id}",
                )
                barrier.wait(timeout=10)
                create_reservation(
                    usuario=user,
                    viaje=trip,
                    origen=origin,
                    destino=destination,
                    pasajeros=[request],
                )
                return "created"
            except SeatUnavailableError:
                return "unavailable"
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    attempt_reservation,
                    (self.user.pk, self.other_user.pk),
                )
            )

        self.assertCountEqual(results, ("created", "unavailable"))
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertEqual(
            DetalleReserva.objects.filter(asiento=self.seat_1a).count(),
            1,
        )
