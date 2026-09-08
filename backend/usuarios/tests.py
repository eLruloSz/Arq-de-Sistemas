from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import path, reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from .permissions import IsAdministrator


User = get_user_model()
TEST_PASSWORD = "Clave-Muy-Segura-2026!"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


class AdminOnlyTestView(APIView):
    permission_classes = (IsAdministrator,)

    def get(self, request):
        return Response({"allowed": True})


urlpatterns = [
    path("test/admin-only/", AdminOnlyTestView.as_view(), name="admin-only"),
]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class RegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse("usuarios:register")
        self.payload = {
            "username": "pasajero",
            "email": "pasajero@example.com",
            "first_name": "Ana",
            "last_name": "Pérez",
            "password": TEST_PASSWORD,
        }

    def register(self, **changes):
        payload = {**self.payload, **changes}
        return self.client.post(self.url, payload, format="json")

    def test_successful_registration_returns_created(self):
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_successful_registration_creates_user(self):
        self.register()

        self.assertTrue(User.objects.filter(username="pasajero").exists())

    def test_registered_user_is_not_staff(self):
        self.register()

        self.assertFalse(User.objects.get(username="pasajero").is_staff)

    def test_registered_user_is_not_superuser(self):
        self.register()

        self.assertFalse(User.objects.get(username="pasajero").is_superuser)

    def test_password_is_hashed(self):
        self.register()
        user = User.objects.get(username="pasajero")

        self.assertNotEqual(user.password, TEST_PASSWORD)
        self.assertTrue(user.check_password(TEST_PASSWORD))

    def test_password_is_not_returned(self):
        response = self.register()

        self.assertNotIn("password", response.data)

    def test_registration_does_not_return_tokens(self):
        response = self.register()

        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="pasajero",
            email="otro@example.com",
            password=TEST_PASSWORD,
        )

        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existente",
            email="pasajero@example.com",
            password=TEST_PASSWORD,
        )

        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_case_insensitive_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existente",
            email="PASAJERO@EXAMPLE.COM",
            password=TEST_PASSWORD,
        )

        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_invalid_password_is_rejected(self):
        response = self.register(password="password")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(username="pasajero").exists())

    def test_email_is_required(self):
        payload = self.payload.copy()
        payload.pop("email")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_username_is_required(self):
        payload = self.payload.copy()
        payload.pop("username")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_password_is_required(self):
        payload = self.payload.copy()
        payload.pop("password")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_client_cannot_register_staff_user(self):
        response = self.register(is_staff=True)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(User.objects.get(username="pasajero").is_staff)

    def test_client_cannot_register_superuser(self):
        response = self.register(is_superuser=True)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(User.objects.get(username="pasajero").is_superuser)

    def test_first_and_last_name_are_optional(self):
        payload = self.payload.copy()
        payload.pop("first_name")
        payload.pop("last_name")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class JwtAuthenticationTests(APITestCase):
    def setUp(self):
        self.url = reverse("usuarios:token")
        self.user = User.objects.create_user(
            username="pasajero",
            email="pasajero@example.com",
            password=TEST_PASSWORD,
        )

    def test_valid_login_returns_access_token(self):
        response = self.client.post(
            self.url,
            {"username": self.user.username, "password": TEST_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_valid_login_returns_refresh_token(self):
        response = self.client.post(
            self.url,
            {"username": self.user.username, "password": TEST_PASSWORD},
            format="json",
        )

        self.assertIn("refresh", response.data)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            self.url,
            {"username": self.user.username, "password": "incorrecta"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user_is_rejected(self):
        response = self.client.post(
            self.url,
            {"username": "inexistente", "password": TEST_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_refresh_returns_new_access_token(self):
        token_response = self.client.post(
            self.url,
            {"username": self.user.username, "password": TEST_PASSWORD},
            format="json",
        )

        response = self.client.post(
            reverse("usuarios:token-refresh"),
            {"refresh": token_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class CurrentUserTests(APITestCase):
    def setUp(self):
        self.url = reverse("usuarios:me")
        self.user = User.objects.create_user(
            username="pasajero",
            email="pasajero@example.com",
            first_name="Ana",
            last_name="Pérez",
            password=TEST_PASSWORD,
        )

    def authenticate(self, user=None):
        token = AccessToken.for_user(user or self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_anonymous_user_receives_unauthorized(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_token_returns_success(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_matches_authenticated_user(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.data["id"], self.user.pk)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)

    def test_password_is_not_exposed(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertNotIn("password", response.data)

    def test_normal_user_role_is_passenger(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.data["role"], "PASAJERO")

    def test_staff_user_role_is_administrator(self):
        self.user.is_staff = True
        self.user.save(update_fields=("is_staff",))
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.data["role"], "ADMINISTRADOR")


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=FAST_HASHERS,
)
class IsAdministratorTests(APITestCase):
    url = "/test/admin-only/"

    def authenticate(self, user):
        token = AccessToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_anonymous_user_is_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_is_rejected(self):
        user = User.objects.create_user(username="pasajero")
        self.authenticate(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_is_accepted(self):
        user = User.objects.create_user(username="staff", is_staff=True)
        self.authenticate(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_is_accepted(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=TEST_PASSWORD,
        )
        self.authenticate(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
