from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from config.test_support import DomainAPITestCase

from .models import Pago, Reserva
from .services import cancel_reservation, pay_reservation


class LifecycleAPITests(DomainAPITestCase):
    def setUp(self):
        super().setUp()
        self.booking = self.create_existing_reservation()

    def post(self, action, body=None, pk=None):
        url = f"/api/v1/bookings/{pk or self.booking.pk}/{action}/"
        if body is None:
            return self.client.post(url)
        return self.client.post(url, body, format="json")

    def test_anonymous_cannot_pay(self):
        self.assertEqual(self.post("pay").status_code, 401)
        self.assertFalse(Pago.objects.exists())

    def test_anonymous_cannot_cancel(self):
        self.assertEqual(self.post("cancel").status_code, 401)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")

    def test_owner_can_pay_without_body(self):
        self.login_as(self.user)
        response = self.post("pay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "CONFIRMADA")
        payment = response.data["payment"]
        self.assertEqual(set(payment), {"id", "amount", "status", "paid_at"})
        self.assertEqual(payment["amount"], response.data["total"])
        self.assertEqual(payment["status"], "APROBADO")
        self.assertIsNotNone(payment["paid_at"])

    def test_admin_can_pay_other_users_booking(self):
        self.login_as(self.admin)
        self.assertEqual(self.post("pay", {}).status_code, 200)

    def test_other_passenger_cannot_pay(self):
        self.login_as(self.other_user)
        self.assertEqual(self.post("pay").status_code, 404)
        self.assertFalse(Pago.objects.exists())

    def test_nonexistent_booking_pay_returns_404(self):
        self.login_as(self.user)
        self.assertEqual(self.post("pay", pk=999999).status_code, 404)

    def test_client_cannot_override_amount_or_payment_state(self):
        self.login_as(self.user)
        response = self.post("pay", {
            "amount": "0.01", "monto": "0.01", "price": "0.01",
            "precio": "0.01", "total": "0.01", "payment_status": "ANULADO",
            "estado_pago": "ANULADO", "status": "CANCELADA",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["payment"]["amount"], "30000.00")
        self.assertEqual(response.data["payment"]["status"], "APROBADO")
        self.assertEqual(response.data["status"], "CONFIRMADA")

    def test_card_and_external_payment_data_rejected(self):
        self.login_as(self.user)
        for field in (
            "card_number", "cvv", "expiration", "holder", "gateway", "transaction_id",
        ):
            with self.subTest(field=field):
                self.assertEqual(self.post("pay", {field: "test"}).status_code, 400)
        self.assertFalse(Pago.objects.exists())
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")

    def test_duplicate_payment_returns_domain_conflict(self):
        self.login_as(self.user)
        self.assertEqual(self.post("pay").status_code, 200)
        response = self.post("pay")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data, {
            "code": "BOOKING_NOT_PAYABLE",
            "message": "The booking cannot be paid in its current state.",
            "details": {"status": "CONFIRMADA"},
        })
        self.assertEqual(Pago.objects.count(), 1)

    def test_cancelled_booking_cannot_be_paid(self):
        cancel_reservation(reservation_id=self.booking.pk)
        self.login_as(self.user)
        response = self.post("pay")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "BOOKING_NOT_PAYABLE")
        self.assertEqual(response.data["details"], {"status": "CANCELADA"})
        self.assertFalse(Pago.objects.exists())

    def test_owner_can_cancel_pending_without_payment(self):
        self.login_as(self.user)
        response = self.post("cancel", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "CANCELADA")
        self.assertIsNone(response.data["payment"])
        self.assertFalse(Pago.objects.exists())

    def test_admin_can_cancel_other_users_booking(self):
        self.login_as(self.admin)
        self.assertEqual(self.post("cancel").status_code, 200)

    def test_other_passenger_cannot_cancel(self):
        self.login_as(self.other_user)
        self.assertEqual(self.post("cancel").status_code, 404)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")

    def test_nonexistent_booking_cancel_returns_404(self):
        self.login_as(self.user)
        self.assertEqual(self.post("cancel", pk=999999).status_code, 404)

    def test_owner_can_cancel_confirmed_and_void_payment(self):
        pay_reservation(reservation_id=self.booking.pk)
        self.login_as(self.user)
        response = self.post("cancel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "CANCELADA")
        self.assertEqual(response.data["payment"]["status"], "ANULADO")
        self.assertEqual(response.data["payment"]["amount"], response.data["total"])

    def test_duplicate_cancellation_returns_domain_conflict(self):
        self.login_as(self.user)
        self.assertEqual(self.post("cancel").status_code, 200)
        original = Reserva.objects.get(pk=self.booking.pk).cancelled_at
        response = self.post("cancel")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data, {
            "code": "BOOKING_NOT_CANCELLABLE",
            "message": "The booking cannot be cancelled in its current state.",
            "details": {"status": "CANCELADA"},
        })
        self.assertEqual(Reserva.objects.get(pk=self.booking.pk).cancelled_at, original)

    def test_inconsistent_confirmed_booking_returns_conflict(self):
        Reserva.objects.filter(pk=self.booking.pk).update(estado="CONFIRMADA")
        self.login_as(self.user)
        response = self.post("cancel")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "BOOKING_NOT_CANCELLABLE")
        self.assertEqual(response.data["details"], {"status": "CONFIRMADA"})

    def test_no_patch_delete_or_get_actions(self):
        self.login_as(self.user)
        detail = f"/api/v1/bookings/{self.booking.pk}/"
        self.assertEqual(self.client.patch(detail, {"status": "CANCELADA"}).status_code, 405)
        self.assertEqual(self.client.delete(detail).status_code, 405)
        for action in ("pay", "cancel"):
            self.assertEqual(self.client.get(f"{detail}{action}/").status_code, 405)

    def test_payment_in_list_and_detail_without_n_plus_one(self):
        self.login_as(self.user)
        detail = f"/api/v1/bookings/{self.booking.pk}/"
        self.assertIsNone(self.client.get(detail).data["payment"])
        pay_reservation(reservation_id=self.booking.pk)
        with CaptureQueriesContext(connection) as first:
            response = self.client.get("/api/v1/bookings/")
        self.assertEqual(response.data["results"][0]["payment"]["status"], "APROBADO")
        other = self.create_existing_reservation(seat=self.seat_1b)
        pay_reservation(reservation_id=other.pk)
        with CaptureQueriesContext(connection) as second:
            response = self.client.get("/api/v1/bookings/")
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(first), len(second))
        self.assertEqual(self.client.get(detail).data["payment"]["status"], "APROBADO")

    def test_openapi_documents_actions_and_nullable_payment(self):
        response = self.client.get(
            "/api/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        for action in ("pay", "cancel"):
            operation = schema["paths"][f"/api/v1/bookings/{{id}}/{action}/"]["post"]
            self.assertNotIn("requestBody", operation)
            self.assertTrue({"200", "401", "404", "409"} <= set(operation["responses"]))
            self.assertTrue(operation["security"])
            self.assertNotIn({}, operation["security"])
        schemas = schema["components"]["schemas"]
        self.assertTrue(schemas["Booking"]["properties"]["payment"]["nullable"])
        self.assertEqual(set(schemas["Payment"]["properties"]), {
            "id", "amount", "status", "paid_at",
        })


class LifecycleAcceptanceTests(DomainAPITestCase):
    @override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
    def test_register_search_book_pay_cancel_and_availability(self):
        credentials = {"username": "lifecycle", "password": "Lifecycle-938!Secret"}
        registered = self.client.post("/api/v1/auth/register/", {
            **credentials, "email": "lifecycle@example.com",
        })
        self.assertEqual(registered.status_code, 201)
        login = self.client.post("/api/v1/auth/token/", credentials)
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        search = self.client.get("/api/v1/trips/search/", self.search_params())
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.data[0]["trip_id"], self.trip.pk)

        def assert_available(expected):
            response = self.client.get(
                f"/api/v1/trips/{self.trip.pk}/availability/", self.search_params(),
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(next(
                seat["available"] for seat in response.data["seats"]
                if seat["id"] == self.seat_1a.pk
            ), expected)

        assert_available(True)
        created = self.client.post("/api/v1/bookings/", self.booking_body(), format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["status"], "PENDIENTE_PAGO")
        self.assertIsNone(created.data["payment"])
        assert_available(False)
        detail = f"/api/v1/bookings/{created.data['id']}/"
        paid = self.client.post(f"{detail}pay/")
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.data["status"], "CONFIRMADA")
        self.assertEqual(paid.data["payment"]["status"], "APROBADO")
        self.assertEqual(paid.data["payment"]["amount"], created.data["total"])
        assert_available(False)
        cancelled = self.client.post(f"{detail}cancel/")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"], "CANCELADA")
        self.assertEqual(cancelled.data["payment"]["status"], "ANULADO")
        assert_available(True)
