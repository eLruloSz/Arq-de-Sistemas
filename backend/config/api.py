"""Utilidades de interfaz REST; no contienen reglas de reservas."""
from copy import copy

from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError
from drf_spectacular.utils import OpenApiResponse
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import exception_handler

from usuarios.permissions import IsAdministrator
from ventas.exceptions import (
    BookingNotCancellableError,
    BookingNotPayableError,
    FareNotFoundError,
    InvalidReservationError,
    InvalidSeatError,
    InvalidSegmentError,
    SeatUnavailableError,
    TripNotAvailableError,
)


DOMAIN_ERRORS = {
    BookingNotPayableError: (409, "BOOKING_NOT_PAYABLE"),
    BookingNotCancellableError: (409, "BOOKING_NOT_CANCELLABLE"),
    InvalidSegmentError: (400, "INVALID_SEGMENT"),
    TripNotAvailableError: (409, "TRIP_NOT_AVAILABLE"),
    FareNotFoundError: (400, "FARE_NOT_FOUND"),
    InvalidSeatError: (400, "INVALID_SEAT"),
    InvalidReservationError: (400, "INVALID_RESERVATION"),
    SeatUnavailableError: (409, "SEAT_NOT_AVAILABLE"),
}


def api_exception_handler(exc, context):
    for error_class, (http_status, code) in DOMAIN_ERRORS.items():
        if isinstance(exc, error_class):
            details = {}
            if hasattr(exc, "status"):
                details["status"] = exc.status
            if hasattr(exc, "seat_ids"):
                details["seat_ids"] = list(exc.seat_ids)
            return Response(
                {"code": code, "message": str(exc), "details": details},
                status=http_status,
            )
    if isinstance(exc, ModelValidationError):
        details = getattr(exc, "message_dict", {"errors": exc.messages})
        return Response(details, status=400)
    if isinstance(exc, IntegrityError):
        return Response(
            {"code": "INTEGRITY_CONFLICT",
             "message": "Los datos incumplen una restricción de integridad.",
             "details": {}},
            status=409,
        )
    return exception_handler(exc, context)


class DomainErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField()


DOMAIN_RESPONSES = {
    400: OpenApiResponse(
        DomainErrorSerializer,
        description="Tramo, tarifa, asiento o solicitud inválidos.",
    ),
    409: OpenApiResponse(
        DomainErrorSerializer,
        description="Viaje no disponible o asiento ocupado.",
    ),
    404: OpenApiResponse(description="Recurso inexistente o no accesible."),
}


class ValidatedModelSerializer(serializers.ModelSerializer):
    """Reutiliza clean() y constraints también para PATCH parcial."""

    def validate(self, attrs):
        instance = copy(self.instance) if self.instance else self.Meta.model()
        for field, value in attrs.items():
            setattr(instance, field, value)
        try:
            instance.full_clean()
        except ModelValidationError as exc:
            names = {field.source: name for name, field in self.fields.items()}
            names["__all__"] = "non_field_errors"
            errors = getattr(exc, "message_dict", {"non_field_errors": exc.messages})
            raise serializers.ValidationError(
                {names.get(field, field): messages
                 for field, messages in errors.items()}
            ) from exc
        return attrs


class AdministrativeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Catálogo administrativo: requiere JWT e is_staff=True.

    POST/PATCH validan campos, reglas del modelo y restricciones (400).
    Anónimo: 401; pasajero: 403; recurso inexistente: 404.
    Las restricciones concurrentes de base de datos devuelven 409.
    No se ofrece eliminación física ni actualización mediante PUT.
    """
    permission_classes = (IsAdministrator,)
    http_method_names = ("get", "post", "patch", "head", "options")


def integer_query(params, name):
    field = serializers.IntegerField(min_value=1, max_value=9223372036854775807)
    try:
        return field.run_validation(params[name])
    except serializers.ValidationError as exc:
        raise serializers.ValidationError({name: exc.detail}) from exc


def boolean_query(params, name):
    value = params[name].lower()
    if value not in ("true", "false"):
        raise serializers.ValidationError({name: "Utilice true o false."})
    return value == "true"
