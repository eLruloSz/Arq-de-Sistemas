from unittest.mock import patch

from django.db import IntegrityError

from config.test_support import DomainAPITestCase

from .models import Parada, Ruta, RutaParada


class StopAPITests(DomainAPITestCase):
    url = "/api/v1/stops/"

    def test_public_get(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_only_active_by_default(self):
        inactive = Parada.objects.create(nombre="Cerrada", ciudad="X", activo=False)
        response = self.client.get(self.url)
        self.assertNotIn(
            inactive.pk, [item["id"] for item in response.data["results"]],
        )
        self.assertEqual(
            self.client.get(f"{self.url}{inactive.pk}/").status_code, 404,
        )

    def test_anonymous_cannot_post(self):
        self.assertEqual(self.client.post(self.url, {}).status_code, 401)

    def test_passenger_cannot_post(self):
        self.login_as(self.user)
        self.assertEqual(self.client.post(self.url, {}).status_code, 403)

    def test_admin_can_post(self):
        self.login_as(self.admin)
        response = self.client.post(
            self.url, {"name": "Terminal", "city": "Temuco"},
        )
        self.assertEqual(response.status_code, 201)

    def test_admin_can_patch(self):
        self.login_as(self.admin)
        pk = self.route_stops[0].parada_id
        response = self.client.patch(f"{self.url}{pk}/", {"active": False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Parada.objects.get(pk=pk).activo)


class RouteAPITests(DomainAPITestCase):
    url = "/api/v1/routes/"

    def test_admin_create_list_patch(self):
        self.login_as(self.admin)
        response = self.client.post(self.url, {"name": "Nueva"})
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.client.patch(f"{self.url}{pk}/", {"active": False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["active"])
        self.assertEqual(self.client.delete(f"{self.url}{pk}/").status_code, 405)

    def test_detail_stops_ordered(self):
        self.login_as(self.admin)
        response = self.client.get(f"{self.url}{self.route.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["order"] for item in response.data["stops"]], list(range(5)),
        )
        self.assertEqual(
            response.data["stops"][0]["stop_id"],
            self.route_stops[0].parada_id,
        )

    def test_passenger_cannot_write(self):
        self.login_as(self.user)
        self.assertEqual(self.client.post(self.url, {}).status_code, 403)


class RouteStopsAPITests(DomainAPITestCase):
    def setUp(self):
        super().setUp()
        self.empty_route = Ruta.objects.create(nombre="Editable")
        RutaParada.objects.create(
            ruta=self.empty_route, parada=self.route_stops[4].parada,
            orden=0, minutos_desde_origen=0,
        )
        self.url = f"/api/v1/routes/{self.empty_route.pk}/stops/"
        self.body = {"stops": [
            {"stop_id": self.route_stops[0].parada_id,
             "order": 0, "minutes_from_origin": 0},
            {"stop_id": self.route_stops[1].parada_id,
             "order": 1, "minutes_from_origin": 360},
        ]}
        self.login_as(self.admin)

    def test_get_ordered(self):
        response = self.client.get(f"/api/v1/routes/{self.route.pk}/stops/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["order"] for row in response.data], list(range(5)))

    def test_put_replaces(self):
        response = self.client.put(self.url, self.body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["stop_id"] for row in response.data],
            [stop["stop_id"] for stop in self.body["stops"]],
        )

    def test_duplicate_stop_rejected(self):
        self.body["stops"][1]["stop_id"] = self.body["stops"][0]["stop_id"]
        self.assertEqual(
            self.client.put(self.url, self.body, format="json").status_code, 400,
        )

    def test_duplicate_order_rejected(self):
        self.body["stops"][1]["order"] = 0
        self.assertEqual(
            self.client.put(self.url, self.body, format="json").status_code, 400,
        )

    def test_nonexistent_stop_preserves_configuration(self):
        original = list(self.empty_route.paradas_ruta.values())
        self.body["stops"][1]["stop_id"] = 999999
        response = self.client.put(self.url, self.body, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(list(self.empty_route.paradas_ruta.values()), original)

    def test_database_failure_rolls_back_delete(self):
        original = list(self.empty_route.paradas_ruta.values())
        with patch(
            "rutas.services.RutaParada.objects.bulk_create",
            side_effect=IntegrityError("fallo de prueba"),
        ):
            response = self.client.put(self.url, self.body, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(list(self.empty_route.paradas_ruta.values()), original)

    def test_route_with_trips_and_fares_protected(self):
        original = list(self.route.paradas_ruta.values())
        response = self.client.put(
            f"/api/v1/routes/{self.route.pk}/stops/", self.body, format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "ROUTE_IN_USE")
        self.assertEqual(list(self.route.paradas_ruta.values()), original)

    def test_passenger_rejected(self):
        self.login_as(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(
            self.client.put(self.url, self.body, format="json").status_code, 403,
        )

    def test_minimum_two_stops(self):
        self.body["stops"].pop()
        self.assertEqual(
            self.client.put(self.url, self.body, format="json").status_code, 400,
        )

    def test_incoherent_order_or_minutes_rejected(self):
        for field, value in (("order", 3), ("minutes_from_origin", -1)):
            with self.subTest(field=field):
                body = {"stops": [dict(item) for item in self.body["stops"]]}
                body["stops"][1][field] = value
                self.assertEqual(
                    self.client.put(self.url, body, format="json").status_code,
                    400,
                )
        self.body["stops"][0]["minutes_from_origin"] = 1
        self.assertEqual(
            self.client.put(self.url, self.body, format="json").status_code, 400,
        )


class FareAPITests(DomainAPITestCase):
    url = "/api/v1/fares/"

    def payload(self):
        return {
            "route": self.route.pk, "origin": self.route_stops[0].pk,
            "destination": self.route_stops[1].pk, "price": "12000.00",
        }

    def test_admin_can_create(self):
        self.login_as(self.admin)
        self.assertEqual(
            self.client.post(self.url, self.payload()).status_code, 201,
        )

    def test_passenger_rejected(self):
        self.login_as(self.user)
        self.assertEqual(
            self.client.post(self.url, self.payload()).status_code, 403,
        )

    def test_model_segment_validation_on_patch(self):
        self.login_as(self.admin)
        response = self.client.patch(
            f"{self.url}{self.fare.pk}/", {"destination": self.route_stops[0].pk},
        )
        self.assertEqual(response.status_code, 400)
        self.fare.refresh_from_db()
        self.assertEqual(self.fare.destino_id, self.route_stops[3].pk)

    def test_nonpositive_price_rejected(self):
        self.login_as(self.admin)
        for price in ("0.00", "-1.00"):
            with self.subTest(price=price):
                self.assertEqual(self.client.post(
                    self.url, {**self.payload(), "price": price},
                ).status_code, 400)

    def test_route_and_active_filters(self):
        self.login_as(self.admin)
        self.assertEqual(
            self.client.get(self.url, {"route": self.route.pk}).data["count"], 1,
        )
        self.assertEqual(
            self.client.get(self.url, {"active": "false"}).data["count"], 0,
        )
