"""Fixtures compartidas exclusivamente por tests de la API."""
from datetime import datetime
from zoneinfo import ZoneInfo

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from ventas.test_services import ReservationServiceFixtures


class DomainAPITestCase(ReservationServiceFixtures, APITestCase):
    def setUp(self):
        super().setUp()
        self.admin = type(self.user).objects.create_user(
            username="administrador", is_staff=True,
        )
        self.trip.fecha_hora_salida = datetime(
            2026, 9, 9, 22, 0, tzinfo=ZoneInfo("America/Santiago"),
        )
        self.trip.save(update_fields=("fecha_hora_salida",))
        self.other_trip.estado = "CANCELADO"
        self.other_trip.save(update_fields=("estado",))

    def login_as(self, user):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}",
        )

    def booking_body(self, seat=None):
        return {
            "trip_id": self.trip.pk,
            "origin_id": self.route_stops[1].parada_id,
            "destination_id": self.route_stops[3].parada_id,
            "passengers": [{
                "seat_id": (seat or self.seat_1a).pk,
                "first_name": "Ana",
                "last_name": "Pérez",
                "document_type": "RUT",
                "document_number": "11111111-1",
            }],
        }

    def search_params(self, **changes):
        return {
            "origin": self.route_stops[1].parada_id,
            "destination": self.route_stops[3].parada_id,
            "date": "2026-09-10",
            **changes,
        }
