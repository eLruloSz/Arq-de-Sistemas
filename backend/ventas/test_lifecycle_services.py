from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from .exceptions import BookingNotCancellableError, BookingNotPayableError
from .models import Pago, Reserva
from .services import (
    cancel_reservation, create_reservation, get_available_seats, pay_reservation,
)
from .test_services import ReservationServiceFixtures


class LifecycleServiceTests(ReservationServiceFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.booking = create_reservation(
            usuario=self.user, viaje=self.trip,
            origen=self.route_stops[1], destino=self.route_stops[3],
            pasajeros=[self.passenger_request()],
        )

    def pay(self):
        return pay_reservation(reservation_id=self.booking.pk)

    def cancel(self):
        return cancel_reservation(reservation_id=self.booking.pk)

    def test_payment_confirms_booking_and_preserves_total(self):
        result = self.pay()
        self.assertEqual(result.pk, self.booking.pk)
        self.assertEqual(result.estado, Reserva.Estado.CONFIRMADA)
        self.assertEqual(result.total, self.booking.total)
        payment = Pago.objects.get(reserva=result)
        self.assertEqual(payment.estado, Pago.Estado.APROBADO)
        self.assertEqual(payment.monto, self.booking.total)
        self.assertIsNotNone(payment.paid_at)
        self.assertIsNone(result.cancelled_at)

    def test_duplicate_payment_preserves_original_payment(self):
        self.pay()
        original = Pago.objects.get(reserva=self.booking)
        with self.assertRaises(BookingNotPayableError) as error:
            self.pay()
        self.assertEqual(error.exception.status, "CONFIRMADA")
        self.assertEqual(Pago.objects.filter(reserva=self.booking).count(), 1)
        self.assertEqual(Pago.objects.get(pk=original.pk).paid_at, original.paid_at)

    def test_confirmed_without_payment_is_not_payable(self):
        Reserva.objects.filter(pk=self.booking.pk).update(estado="CONFIRMADA")
        with self.assertRaises(BookingNotPayableError):
            self.pay()
        self.assertFalse(Pago.objects.exists())

    def test_cancelled_booking_is_not_payable(self):
        self.cancel()
        with self.assertRaises(BookingNotPayableError) as error:
            self.pay()
        self.assertEqual(error.exception.status, "CANCELADA")
        self.assertFalse(Pago.objects.exists())

    def test_voided_payment_cannot_be_paid_again(self):
        self.pay()
        self.cancel()
        original = list(Pago.objects.values())
        with self.assertRaises(BookingNotPayableError):
            self.pay()
        self.assertEqual(list(Pago.objects.values()), original)

    def test_compatible_pending_payment_is_reused(self):
        payment = Pago.objects.create(reserva=self.booking, monto=self.booking.total)
        self.pay()
        payment.refresh_from_db()
        self.assertEqual(payment.estado, "APROBADO")
        self.assertEqual(Pago.objects.count(), 1)

    def test_incompatible_existing_payments_are_unchanged(self):
        cases = (
            {"estado": "APROBADO"}, {"estado": "ANULADO"},
            {"monto": Decimal("1")}, {"paid_at": timezone.now()},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                payment = Pago.objects.create(**{
                    "reserva": self.booking, "monto": self.booking.total, **changes,
                })
                original = list(Pago.objects.values())
                with self.assertRaises(BookingNotPayableError):
                    self.pay()
                self.assertEqual(list(Pago.objects.values()), original)
                self.booking.refresh_from_db()
                self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")
                payment.delete()

    def test_payment_rolls_back_when_booking_save_fails(self):
        with patch.object(Reserva, "save", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.pay()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")
        self.assertFalse(Pago.objects.exists())

    def test_reused_payment_update_rolls_back(self):
        payment = Pago.objects.create(reserva=self.booking, monto=self.booking.total)
        with patch.object(Reserva, "full_clean", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.pay()
        payment.refresh_from_db()
        self.assertEqual(payment.estado, "PENDIENTE")
        self.assertIsNone(payment.paid_at)

    def test_payment_validation_failure_leaves_booking_pending(self):
        with patch.object(Pago, "full_clean", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.pay()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")
        self.assertFalse(Pago.objects.exists())

    def test_cancel_pending_creates_no_payment(self):
        result = self.cancel()
        self.assertEqual(result.estado, "CANCELADA")
        self.assertIsNotNone(result.cancelled_at)
        self.assertEqual(result.total, self.booking.total)
        self.assertFalse(Pago.objects.exists())

    def test_cancel_confirmed_voids_payment_preserving_amount_and_paid_at(self):
        self.pay()
        original = Pago.objects.get(reserva=self.booking)
        result = self.cancel()
        payment = Pago.objects.get(reserva=self.booking)
        self.assertEqual(result.estado, "CANCELADA")
        self.assertIsNotNone(result.cancelled_at)
        self.assertEqual(payment.estado, "ANULADO")
        self.assertEqual(payment.monto, original.monto)
        self.assertEqual(payment.paid_at, original.paid_at)

    def test_duplicate_cancellation_preserves_timestamp(self):
        original = self.cancel().cancelled_at
        with self.assertRaises(BookingNotCancellableError) as error:
            self.cancel()
        self.assertEqual(error.exception.status, "CANCELADA")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.cancelled_at, original)

    def test_confirmed_without_payment_cannot_be_cancelled(self):
        Reserva.objects.filter(pk=self.booking.pk).update(estado="CONFIRMADA")
        with self.assertRaises(BookingNotCancellableError):
            self.cancel()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "CONFIRMADA")
        self.assertIsNone(self.booking.cancelled_at)
        self.assertFalse(Pago.objects.exists())

    def test_confirmed_inconsistent_payment_cannot_be_cancelled(self):
        self.pay()
        payment = Pago.objects.get(reserva=self.booking)
        for changes in (
            {"estado": "PENDIENTE"}, {"estado": "ANULADO"},
            {"monto": Decimal("1")}, {"paid_at": None},
        ):
            with self.subTest(changes=changes):
                Pago.objects.filter(pk=payment.pk).update(
                    **{"estado": "APROBADO", "monto": self.booking.total,
                       "paid_at": payment.paid_at, **changes},
                )
                original = list(Pago.objects.values())
                with self.assertRaises(BookingNotCancellableError):
                    self.cancel()
                self.assertEqual(list(Pago.objects.values()), original)
                self.booking.refresh_from_db()
                self.assertEqual(self.booking.estado, "CONFIRMADA")
                self.assertIsNone(self.booking.cancelled_at)

    def test_pending_with_payment_cannot_be_cancelled(self):
        Pago.objects.create(reserva=self.booking, monto=self.booking.total)
        with self.assertRaises(BookingNotCancellableError):
            self.cancel()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "PENDIENTE_PAGO")
        self.assertIsNone(self.booking.cancelled_at)
        self.assertEqual(Pago.objects.get(reserva=self.booking).estado, "PENDIENTE")

    def test_cancellation_rolls_back_payment_void_on_booking_save_failure(self):
        self.pay()
        with patch.object(Reserva, "save", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.cancel()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.estado, "CONFIRMADA")
        self.assertIsNone(self.booking.cancelled_at)
        self.assertEqual(Pago.objects.get(reserva=self.booking).estado, "APROBADO")

    def test_payment_does_not_change_availability_and_cancellation_releases(self):
        def available():
            return get_available_seats(
                viaje=self.trip, origen=self.route_stops[2],
                destino=self.route_stops[4],
            ).filter(pk=self.seat_1a.pk).exists()
        self.assertFalse(available())
        self.pay()
        self.assertFalse(available())
        self.cancel()
        self.assertTrue(available())

    def test_pending_cancellation_releases_overlapping_segment(self):
        self.cancel()
        self.assertTrue(get_available_seats(
            viaje=self.trip, origen=self.route_stops[2], destino=self.route_stops[4],
        ).filter(pk=self.seat_1a.pk).exists())


class LifecycleConcurrencyTests(ReservationServiceFixtures, TransactionTestCase):
    def run_concurrent(self, service, error_type):
        self.assertEqual(connection.vendor, "postgresql")
        booking = self.create_existing_reservation()
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '5s'")
                barrier.wait(timeout=10)
                result = service(reservation_id=booking.pk)
                return ("success", result.cancelled_at)
            except error_type as error:
                return ("conflict", error.status)
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(attempt) for _ in range(2)]
            results = [future.result(timeout=15) for future in futures]
        self.assertCountEqual([row[0] for row in results], ["success", "conflict"])
        booking.refresh_from_db()
        return booking, dict(results)

    def test_double_payment_creates_exactly_one_payment(self):
        booking, results = self.run_concurrent(pay_reservation, BookingNotPayableError)
        self.assertEqual(booking.estado, "CONFIRMADA")
        self.assertEqual(results["conflict"], "CONFIRMADA")
        self.assertEqual(Pago.objects.filter(reserva=booking).count(), 1)
        self.assertEqual(booking.pago.estado, "APROBADO")

    def test_double_cancellation_preserves_winning_timestamp(self):
        booking, results = self.run_concurrent(
            cancel_reservation, BookingNotCancellableError,
        )
        self.assertEqual(booking.estado, "CANCELADA")
        self.assertEqual(results["conflict"], "CANCELADA")
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(booking.cancelled_at, results["success"])
        self.assertFalse(Pago.objects.filter(reserva=booking).exists())
