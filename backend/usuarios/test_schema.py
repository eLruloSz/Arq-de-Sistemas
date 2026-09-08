from rest_framework.test import APITestCase

from config.test_support import DomainAPITestCase


REST_FIELDS = {
    "Bus": {"id", "license_plate", "internal_number", "brand", "model", "active", "created_at"},
    "Seat": {"id", "bus", "number", "row", "column", "active"},
    "Stop": {"id", "name", "city", "address", "active"},
    "Route": {"id", "name", "active", "created_at", "stops"},
    "Fare": {"id", "route", "origin", "destination", "price", "active"},
    "Trip": {"id", "route", "bus", "departure_datetime", "status", "created_at"},
    "RouteStop": {"route_stop_id", "stop_id", "name", "city", "order", "minutes_from_origin"},
}


class OpenAPITests(APITestCase):
    def test_english_fields_in_response_and_write_schemas(self):
        schema = self.schema()
        components = schema["components"]["schemas"]
        for name, fields in REST_FIELDS.items():
            with self.subTest(schema=name):
                self.assertEqual(set(components[name]["properties"]), fields)
            if name == "RouteStop":
                continue
            writable = fields - {"id", "created_at", "stops"}
            for request_name in (f"{name}Request", f"Patched{name}Request"):
                with self.subTest(schema=request_name):
                    self.assertEqual(
                        set(components[request_name]["properties"]), writable,
                    )
        params = schema["paths"]["/api/v1/seats/"]["get"]["parameters"]
        names = {param["name"] for param in params}
        self.assertIn("active", names)
        self.assertNotIn("activo", names)

    def schema(self):
        response = self.client.get(
            "/api/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_schema_contains_expected_paths(self):
        paths = self.schema()["paths"]
        for path in (
            "/api/v1/auth/register/", "/api/v1/auth/token/",
            "/api/v1/stops/", "/api/v1/trips/search/",
            "/api/v1/trips/{id}/availability/", "/api/v1/bookings/",
        ):
            with self.subTest(path=path):
                self.assertIn(path, paths)

    def test_jwt_bearer_declared(self):
        schema = self.schema()
        schemes = schema["components"]["securitySchemes"]
        bearer_keys = [
            key for key, value in schemes.items()
            if value["type"] == "http" and value["scheme"] == "bearer"
        ]
        self.assertTrue(bearer_keys)
        security = schema["paths"]["/api/v1/bookings/"]["post"]["security"]
        self.assertTrue(any(key in item for key in bearer_keys for item in security))

    def test_swagger_html_and_schema_url(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SwaggerUIBundle")
        self.assertContains(response, "/api/schema/")

    def test_booking_body_and_conflict_documented(self):
        operation = self.schema()["paths"]["/api/v1/bookings/"]["post"]
        self.assertIn("requestBody", operation)
        self.assertIn("201", operation["responses"])
        self.assertIn("409", operation["responses"])

    def test_search_parameters_documented(self):
        operation = self.schema()["paths"]["/api/v1/trips/search/"]["get"]
        params = {param["name"]: param for param in operation["parameters"]}
        for name in ("origin", "destination", "date"):
            self.assertTrue(params[name]["required"])


class RESTFieldContractTests(DomainAPITestCase):
    def test_english_response_fields(self):
        self.login_as(self.admin)
        resources = (
            ("buses", self.bus.pk, "Bus"),
            ("seats", self.seat_1a.pk, "Seat"),
            ("stops", self.route_stops[0].parada_id, "Stop"),
            ("routes", self.route.pk, "Route"),
            ("fares", self.fare.pk, "Fare"),
            ("trips", self.trip.pk, "Trip"),
        )
        for resource, pk, name in resources:
            with self.subTest(resource=resource):
                response = self.client.get(f"/api/v1/{resource}/{pk}/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.data), REST_FIELDS[name])
                if name == "Route":
                    self.assertTrue(response.data["stops"])
                    for stop in response.data["stops"]:
                        self.assertEqual(set(stop), REST_FIELDS["RouteStop"])

    def test_validation_errors_use_external_field_names(self):
        self.login_as(self.admin)
        response = self.client.post("/api/v1/buses/", {
            "license_plate": self.bus.patente,
            "internal_number": "unique-test-number",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("license_plate", response.data)
        self.assertNotIn("patente", response.data)
        response = self.client.patch(
            f"/api/v1/fares/{self.fare.pk}/",
            {"destination": self.fare.origen_id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("destination", response.data)
        self.assertNotIn("destino", response.data)
