from config.test_support import DomainAPITestCase

from .models import Bus


class BusAPITests(DomainAPITestCase):
    url = "/api/v1/buses/"

    def test_anonymous_cannot_list(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_passenger_cannot_list(self):
        self.login_as(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_can_list_paginated(self):
        self.login_as(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_admin_can_create(self):
        self.login_as(self.admin)
        response = self.client.post(
            self.url, {"license_plate": "IJKL56", "internal_number": "14"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Bus.objects.filter(pk=response.data["id"]).exists())

    def test_passenger_cannot_create(self):
        self.login_as(self.user)
        response = self.client.post(
            self.url, {"license_plate": "IJKL56", "internal_number": "14"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_patch_and_retrieve(self):
        self.login_as(self.admin)
        url = f"{self.url}{self.bus.pk}/"
        response = self.client.patch(url, {"active": False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.get(url).data["active"])

    def test_no_delete_or_put(self):
        self.login_as(self.admin)
        url = f"{self.url}{self.bus.pk}/"
        self.assertEqual(self.client.delete(url).status_code, 405)
        self.assertEqual(self.client.put(url, {}).status_code, 405)
        self.assertTrue(Bus.objects.filter(pk=self.bus.pk).exists())


class SeatAPITests(DomainAPITestCase):
    url = "/api/v1/seats/"

    def test_admin_can_create(self):
        self.login_as(self.admin)
        response = self.client.post(self.url, {
            "bus": self.bus.pk, "number": "3A", "row": 3, "column": 1,
        })
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("ocupado", response.data)

    def test_passenger_cannot_create(self):
        self.login_as(self.user)
        self.assertEqual(self.client.post(self.url, {}).status_code, 403)

    def test_filter_bus(self):
        self.login_as(self.admin)
        response = self.client.get(self.url, {"bus": self.other_bus.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in response.data["results"]],
            [self.other_bus_seat.pk],
        )

    def test_filter_active(self):
        self.login_as(self.admin)
        response = self.client.get(self.url, {"active": "false"})
        self.assertEqual(
            [row["id"] for row in response.data["results"]],
            [self.inactive_seat.pk],
        )

    def test_invalid_filters_return_400(self):
        self.login_as(self.admin)
        for params in ({"bus": "abc"}, {"active": "invalid"}):
            with self.subTest(params=params):
                self.assertEqual(
                    self.client.get(self.url, params).status_code, 400,
                )

    def test_model_constraints_apply_on_create_and_patch(self):
        self.login_as(self.admin)
        response = self.client.post(self.url, {
            "bus": self.bus.pk, "number": "invalid", "row": 0, "column": 1,
        })
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(
            f"{self.url}{self.seat_1b.pk}/", {"column": 1},
        )
        self.assertEqual(response.status_code, 400)
