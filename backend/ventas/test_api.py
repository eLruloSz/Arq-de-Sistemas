from decimal import Decimal

from django.test import override_settings

from config.test_support import DomainAPITestCase
from rutas.models import Tarifa

from .models import Pago, Reserva


class BookingAPITests(DomainAPITestCase):
    url = "/api/v1/bookings/"

    def setUp(self):
        super().setUp()
        self.login_as(self.user)

    def post(self, **changes):
        return self.client.post(
            self.url, {**self.booking_body(), **changes}, format="json",
        )

    def test_anonymous_rejected(self):
        self.client.credentials()
        self.assertEqual(self.post().status_code, 401)

    def test_authenticated_creates_reservation(self):
        response = self.post()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Reserva.objects.filter(pk=response.data["id"]).exists())
        self.assertFalse(Pago.objects.exists())

    def test_owner_is_request_user(self):
        response = self.post()
        self.assertEqual(
            Reserva.objects.get(pk=response.data["id"]).usuario_id, self.user.pk,
        )

    def test_cannot_force_owner(self):
        response = self.post(user=self.other_user.pk, usuario=self.other_user.pk)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Reserva.objects.get(pk=response.data["id"]).usuario_id, self.user.pk,
        )

    def test_cannot_force_price(self):
        body = self.booking_body()
        body["passengers"][0]["precio_unitario"] = "1.00"
        response = self.post(
            passengers=body["passengers"], price="1.00", precio="1.00",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["passengers"][0]["price"], "30000.00")

    def test_cannot_force_total(self):
        response = self.post(total="1.00")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total"], "30000.00")

    def test_cannot_force_state(self):
        response = self.post(status="CONFIRMADA", estado="CONFIRMADA")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "PENDIENTE_PAGO")

    def test_multiple_passengers_total_and_unit_prices(self):
        passengers = [
            self.booking_body()["passengers"][0],
            self.booking_body(self.seat_1b)["passengers"][0],
        ]
        response = self.post(passengers=passengers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total"], "60000.00")
        self.assertEqual(len(response.data["passengers"]), 2)
        self.assertEqual(
            {row["price"] for row in response.data["passengers"]}, {"30000.00"},
        )

    def test_occupied_seat_conflict_with_ids(self):
        self.create_existing_reservation()
        response = self.post()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "SEAT_NOT_AVAILABLE")
        self.assertEqual(response.data["details"]["seat_ids"], [self.seat_1a.pk])
        self.assertEqual(Reserva.objects.count(), 1)

    def test_invalid_segment(self):
        response = self.post(
            origin_id=self.route_stops[3].parada_id,
            destination_id=self.route_stops[1].parada_id,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_SEGMENT")

    def test_missing_fare(self):
        self.fare.delete()
        response = self.post()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "FARE_NOT_FOUND")

    def test_nonprogrammed_trip(self):
        self.trip.estado = "CANCELADO"
        self.trip.save()
        response = self.post()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "TRIP_NOT_AVAILABLE")

    def test_invalid_seat(self):
        passengers = self.booking_body(self.other_bus_seat)["passengers"]
        response = self.post(passengers=passengers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_SEAT")

    def test_nonexistent_seat(self):
        passengers = self.booking_body()["passengers"]
        passengers[0]["seat_id"] = 999999
        self.assertEqual(self.post(passengers=passengers).status_code, 400)

    def test_input_shape_validation(self):
        for passengers in ([], [{"seat_id": self.seat_1a.pk}]):
            with self.subTest(passengers=passengers):
                self.assertEqual(self.post(passengers=passengers).status_code, 400)
        self.assertFalse(Reserva.objects.exists())

    def test_admin_can_book(self):
        self.login_as(self.admin)
        response = self.post()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Reserva.objects.get(pk=response.data["id"]).usuario_id, self.admin.pk,
        )

    def test_modification_not_exposed(self):
        reservation = self.create_existing_reservation()
        url = f"{self.url}{reservation.pk}/"
        self.assertEqual(self.client.patch(url, {}).status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)


class BookingPrivacyAPITests(DomainAPITestCase):
    def setUp(self):
        super().setUp()
        self.reservation_a = self.create_existing_reservation()
        self.reservation_b = self.create_existing_reservation(seat=self.seat_1b)
        self.reservation_b.usuario = self.other_user
        self.reservation_b.save()
        self.login_as(self.user)

    def test_list_only_own(self):
        response = self.client.get("/api/v1/bookings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.reservation_a.pk)

    def test_other_booking_returns_404(self):
        response = self.client.get(
            f"/api/v1/bookings/{self.reservation_b.pk}/",
        )
        self.assertEqual(response.status_code, 404)

    def test_owner_can_retrieve(self):
        response = self.client.get(f"/api/v1/bookings/{self.reservation_a.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_admin_can_list_and_retrieve_any(self):
        self.login_as(self.admin)
        response = self.client.get("/api/v1/bookings/")
        self.assertEqual(response.data["count"], 2)
        for reservation in (self.reservation_a, self.reservation_b):
            self.assertEqual(self.client.get(
                f"/api/v1/bookings/{reservation.pk}/",
            ).status_code, 200)

    def test_list_query_count_is_bounded(self):
        self.login_as(self.admin)
        with self.assertNumQueries(4):
            response = self.client.get("/api/v1/bookings/")
            self.assertEqual(response.status_code, 200)


class BookingAcceptanceAPITests(DomainAPITestCase):
    @override_settings(
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
    def test_complete_http_flow(self):
        response = self.client.post("/api/v1/auth/register/", {
            "username": "nuevo", "email": "nuevo@example.com",
            "password": "Una-Clave-Larga-946!",
        })
        self.assertEqual(response.status_code, 201)
        response = self.client.post("/api/v1/auth/token/", {
            "username": "nuevo", "password": "Una-Clave-Larga-946!",
        })
        self.assertEqual(response.status_code, 200)
        token = response.data["access"]
        self.assertEqual(self.client.get("/api/v1/stops/").status_code, 200)
        search = self.client.get("/api/v1/trips/search/", self.search_params())
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.data[0]["trip_id"], self.trip.pk)
        url = f"/api/v1/trips/{self.trip.pk}/availability/"
        before = self.client.get(url, self.search_params())
        self.assertTrue(next(
            seat["available"] for seat in before.data["seats"]
            if seat["id"] == self.seat_1a.pk
        ))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        booking = self.client.post(
            "/api/v1/bookings/", self.booking_body(), format="json",
        )
        self.assertEqual(booking.status_code, 201)
        self.assertEqual(
            self.client.get("/api/v1/bookings/").data["results"][0]["id"],
            booking.data["id"],
        )
        for start, end, available in ((2, 4, False), (3, 4, True)):
            Tarifa.objects.create(
                ruta=self.route, origen=self.route_stops[start],
                destino=self.route_stops[end], precio=Decimal("25000"),
            )
            response = self.client.get(url, {
                "origin": self.route_stops[start].parada_id,
                "destination": self.route_stops[end].parada_id,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(next(
                seat["available"] for seat in response.data["seats"]
                if seat["id"] == self.seat_1a.pk
            ), available)
