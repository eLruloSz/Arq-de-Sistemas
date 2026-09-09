from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    message = "Se requiere un usuario administrador."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
