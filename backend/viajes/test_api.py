from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from config.test_support import DomainAPITestCase
from rutas.models import Parada, Tarifa
from ventas.models import Reserva

from .models import Viaje


class TripAdminAPITests(DomainAPITestCase):
    url = "/api/v1/trips/"

    def test_admin_creates_programmed_trip(self):
        self.login_as(self.admin)
        response = self.client.post(self.url, {
            "route": self.route.pk, "bus": self.bus.pk,
            "departure_datetime": "2026-09-10T10:00:00-03:00",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "PROGRAMADO")

    def test_passenger_rejected(self):
        self.login_as(self.user)
        self.assertEqual(self.client.post(self.url, {}).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_can_patch_and_retrieve_state(self):
        self.login_as(self.admin)
        url = f"{self.url}{self.trip.pk}/"
        self.assertEqual(
            self.client.patch(url, {"status": "CANCELADO"}).status_code, 200,
        )
        self.assertEqual(self.client.get(url).data["status"], "CANCELADO")
        self.assertEqual(self.client.delete(url).status_code, 405)


class TripSearchAPITests(DomainAPITestCase):
    url = "/api/v1/trips/search/"

    def search(self, **changes):
        return self.client.get(self.url, self.search_params(**changes))

    def test_public_search_contains_programmed_trip(self):
        response = self.search()
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["trip_id"] for row in response.data], [self.trip.pk])

    def test_both_stops_must_belong_to_route(self):
        other = Parada.objects.create(nombre="Ajena", ciudad="Temuco")
        self.assertEqual(self.search(origin=other.pk).data, [])
        self.assertEqual(self.search(destination=other.pk).data, [])

    def test_reverse_segment_does_not_return_trip(self):
        # Incluso datos de tarifa insertados sin clean no eluden el servicio.
        Tarifa.objects.create(
            ruta=self.route, origen=self.route_stops[3],
            destino=self.route_stops[1], precio=Decimal("30000"),
        )
        response = self.search(
            origin=self.route_stops[3].parada_id,
            destination=self.route_stops[1].parada_id,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_equal_stops_return_400(self):
        response = self.search(destination=self.route_stops[1].parada_id)
        self.assertEqual(response.status_code, 400)

    def test_cancelled_trip_excluded(self):
        self.trip.estado = Viaje.Estado.CANCELADO
        self.trip.save()
        self.assertEqual(self.search().data, [])

    def test_in_progress_trip_excluded(self):
        self.trip.estado = Viaje.Estado.EN_CURSO
        self.trip.save()
        self.assertEqual(self.search().data, [])

    def test_finished_trip_excluded(self):
        self.trip.estado = Viaje.Estado.FINALIZADO
        self.trip.save()
        self.assertEqual(self.search().data, [])

    def test_inactive_route_excluded(self):
        self.route.activa = False
        self.route.save()
        self.assertEqual(self.search().data, [])

    def test_missing_fare_excluded(self):
        self.fare.delete()
        self.assertEqual(self.search().data, [])

    def test_inactive_fare_excluded(self):
        self.fare.activa = False
        self.fare.save()
        self.assertEqual(self.search().data, [])

    def test_different_dates_filter_trips(self):
        self.other_trip.estado = Viaje.Estado.PROGRAMADO
        self.other_trip.fecha_hora_salida = self.trip.fecha_hora_salida.replace(
            day=10,
        )
        self.other_trip.save()
        self.assertEqual(
            [row["trip_id"] for row in self.search().data], [self.trip.pk],
        )
        self.assertEqual(
            [row["trip_id"] for row in self.search(date="2026-09-11").data],
            [self.other_trip.pk],
        )

    def test_previous_day_departure_found_from_intermediate_origin(self):
        response = self.search()
        departure = datetime.fromisoformat(
            response.data[0]["departure_datetime"],
        )
        self.assertEqual(departure.isoformat(), "2026-09-10T04:00:00-03:00")
        self.assertEqual(self.search(date="2026-09-09").data, [])

    def test_arrival_at_destination(self):
        arrival = datetime.fromisoformat(
            self.search().data[0]["arrival_datetime"],
        )
        self.assertEqual(arrival.isoformat(), "2026-09-10T14:00:00-03:00")

    def test_search_uses_elapsed_minutes_across_daylight_saving_change(self):
        self.trip.fecha_hora_salida = datetime(
            2026, 4, 4, 18, 30, tzinfo=ZoneInfo("America/Santiago"),
        )
        self.trip.save()
        response = self.search(date="2026-04-04")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            datetime.fromisoformat(
                response.data[0]["departure_datetime"],
            ).isoformat(),
            "2026-04-04T23:30:00-04:00",
        )

    def test_price(self):
        self.assertEqual(self.search().data[0]["price"], "30000.00")

    def test_available_seats_uses_service(self):
        self.assertEqual(self.search().data[0]["available_seats"], 2)
        self.create_existing_reservation()
        self.assertEqual(self.search().data[0]["available_seats"], 1)

    def test_required_query_parameters(self):
        for key in ("origin", "destination", "date"):
            with self.subTest(key=key):
                params = self.search_params()
                params.pop(key)
                self.assertEqual(
                    self.client.get(self.url, params).status_code, 400,
                )

    def test_invalid_date(self):
        for value in ("invalid", "2026-02-30", ""):
            with self.subTest(value=value):
                self.assertEqual(self.search(date=value).status_code, 400)

    def test_nonexistent_stop_returns_400(self):
        self.assertEqual(self.search(origin=999999).status_code, 400)


class AvailabilityAPITests(DomainAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = f"/api/v1/trips/{self.trip.pk}/availability/"
        for start, end in ((0, 1), (3, 4), (2, 4)):
            Tarifa.objects.create(
                ruta=self.route, origen=self.route_stops[start],
                destino=self.route_stops[end], precio=Decimal("25000"),
            )

    def availability(self, start=1, end=3, **params):
        return self.client.get(self.url, {
            "origin": self.route_stops[start].parada_id,
            "destination": self.route_stops[end].parada_id,
            **params,
        })

    def seat(self, response):
        return next(
            row for row in response.data["seats"] if row["id"] == self.seat_1a.pk
        )

    def test_public_available_seat(self):
        response = self.availability()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.seat(response)["available"])
        self.assertEqual(self.seat(response)["number"], "1A")

    def test_pending_blocks(self):
        self.create_existing_reservation()
        self.assertFalse(self.seat(self.availability())["available"])

    def test_confirmed_blocks(self):
        self.create_existing_reservation(state=Reserva.Estado.CONFIRMADA)
        self.assertFalse(self.seat(self.availability())["available"])

    def test_cancelled_does_not_block(self):
        self.create_existing_reservation(state=Reserva.Estado.CANCELADA)
        self.assertTrue(self.seat(self.availability())["available"])

    def test_previous_segment_free(self):
        self.create_existing_reservation()
        self.assertTrue(self.seat(self.availability(0, 1))["available"])

    def test_next_segment_free(self):
        self.create_existing_reservation()
        self.assertTrue(self.seat(self.availability(3, 4))["available"])

    def test_overlapping_segment_occupied(self):
        self.create_existing_reservation()
        self.assertFalse(self.seat(self.availability(2, 4))["available"])

    def test_inactive_seats_excluded(self):
        ids = [row["id"] for row in self.availability().data["seats"]]
        self.assertNotIn(self.inactive_seat.pk, ids)
        self.assertNotIn(self.other_bus_seat.pk, ids)

    def test_nonexistent_trip(self):
        self.assertEqual(self.client.get(
            "/api/v1/trips/999999/availability/", self.search_params(),
        ).status_code, 404)

    def test_stop_outside_route(self):
        other = Parada.objects.create(nombre="Otra", ciudad="X")
        response = self.availability(origin=other.pk)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_SEGMENT")

    def test_reverse_segment(self):
        response = self.availability(3, 1)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_SEGMENT")

    def test_price(self):
        self.assertEqual(self.availability().data["price"], "30000.00")

    def test_missing_fare(self):
        self.fare.delete()
        response = self.availability()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "FARE_NOT_FOUND")

    def test_nonprogrammed_trip(self):
        self.trip.estado = Viaje.Estado.CANCELADO
        self.trip.save()
        response = self.availability()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "TRIP_NOT_AVAILABLE")

    def test_invalid_parameters(self):
        self.assertEqual(self.client.get(self.url).status_code, 400)
        self.assertEqual(self.availability(origin="bad").status_code, 400)
