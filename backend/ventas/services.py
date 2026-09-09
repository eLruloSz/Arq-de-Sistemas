from collections import Counter
from collections.abc import Sequence

from django.db import transaction
from django.utils import timezone

from flota.models import Asiento
from rutas.models import RutaParada, Tarifa
from viajes.models import Viaje

from .exceptions import (
    BookingNotCancellableError,
    BookingNotPayableError,
    FareNotFoundError,
    InvalidReservationError,
    InvalidSeatError,
    InvalidSegmentError,
    SeatUnavailableError,
    TripNotAvailableError,
)
from .models import DetalleReserva, Pago, Pasajero, Reserva


BLOCKING_RESERVATION_STATES = (
    Reserva.Estado.PENDIENTE_PAGO,
    Reserva.Estado.CONFIRMADA,
)

REQUIRED_PASSENGER_FIELDS = (
    "asiento_id",
    "nombre",
    "apellido",
    "tipo_documento",
    "documento",
)


def validate_segment(*, viaje, origen, destino):
    """Valida que origen y destino definan un tramo posterior en la ruta."""
    if not isinstance(viaje, Viaje) or not viaje.pk:
        raise InvalidSegmentError("El viaje no es válido.")

    if (
        not isinstance(origen, RutaParada)
        or not origen.pk
        or not isinstance(destino, RutaParada)
        or not destino.pk
    ):
        raise InvalidSegmentError("El origen y el destino no son válidos.")

    if origen.ruta_id != viaje.ruta_id:
        raise InvalidSegmentError("El origen no pertenece a la ruta del viaje.")

    if destino.ruta_id != viaje.ruta_id:
        raise InvalidSegmentError("El destino no pertenece a la ruta del viaje.")

    if origen.pk == destino.pk:
        raise InvalidSegmentError("El origen y el destino deben ser distintos.")

    if origen.orden >= destino.orden:
        raise InvalidSegmentError("El origen debe ser anterior al destino.")


def _validate_trip_available(viaje):
    if viaje.estado != Viaje.Estado.PROGRAMADO:
        raise TripNotAvailableError(
            "Solo los viajes programados admiten reservas."
        )


def _get_unavailable_seat_ids_for_valid_segment(*, viaje, origen, destino):
    return set(
        DetalleReserva.objects.filter(
            reserva__viaje=viaje,
            reserva__estado__in=BLOCKING_RESERVATION_STATES,
            reserva__origen__orden__lt=destino.orden,
            reserva__destino__orden__gt=origen.orden,
        )
        .values_list("asiento_id", flat=True)
        .distinct()
    )


def get_unavailable_seat_ids(*, viaje, origen, destino):
    """Devuelve los IDs ocupados para un viaje y tramo válidos."""
    validate_segment(viaje=viaje, origen=origen, destino=destino)
    return _get_unavailable_seat_ids_for_valid_segment(
        viaje=viaje,
        origen=origen,
        destino=destino,
    )


def get_available_seats(*, viaje, origen, destino):
    """Devuelve los asientos activos y libres del bus para el tramo."""
    validate_segment(viaje=viaje, origen=origen, destino=destino)
    _validate_trip_available(viaje)
    unavailable_ids = _get_unavailable_seat_ids_for_valid_segment(
        viaje=viaje,
        origen=origen,
        destino=destino,
    )
    return (
        Asiento.objects.filter(bus_id=viaje.bus_id, activo=True)
        .exclude(pk__in=unavailable_ids)
        .order_by("fila", "columna", "numero")
    )


def _validate_passenger_requests(passengers):
    if (
        not isinstance(passengers, Sequence)
        or isinstance(passengers, (str, bytes))
        or not passengers
    ):
        raise InvalidReservationError(
            "La reserva debe incluir al menos un pasajero."
        )

    normalized = []
    for passenger in passengers:
        if not isinstance(passenger, dict):
            raise InvalidReservationError(
                "Cada pasajero debe representarse mediante un diccionario."
            )

        missing = [
            field
            for field in REQUIRED_PASSENGER_FIELDS
            if field not in passenger or passenger[field] in (None, "")
        ]
        if missing:
            raise InvalidReservationError(
                f"Faltan datos del pasajero: {', '.join(missing)}."
            )

        if passenger["tipo_documento"] not in Pasajero.TipoDocumento.values:
            raise InvalidReservationError("El tipo de documento no es válido.")

        normalized.append(
            {field: passenger[field] for field in REQUIRED_PASSENGER_FIELDS}
        )

    seat_ids = [passenger["asiento_id"] for passenger in normalized]
    try:
        seat_id_counts = Counter(seat_ids)
    except TypeError as error:
        raise InvalidSeatError(
            seat_ids=(),
            message="Los identificadores de asiento no son válidos.",
        ) from error

    duplicate_ids = {
        seat_id for seat_id, count in seat_id_counts.items() if count > 1
    }
    if duplicate_ids:
        raise InvalidSeatError(
            duplicate_ids,
            "No se puede repetir un asiento en la misma solicitud.",
        )

    return normalized, set(seat_id_counts)


def _get_valid_seats(*, seat_ids, viaje):
    try:
        seats_by_id = Asiento.objects.filter(pk__in=seat_ids).in_bulk()
    except (TypeError, ValueError) as error:
        raise InvalidSeatError(
            seat_ids=(),
            message="Los identificadores de asiento no son válidos.",
        ) from error

    invalid_ids = set(seat_ids) - set(seats_by_id)
    invalid_ids.update(
        seat_id
        for seat_id, seat in seats_by_id.items()
        if not seat.activo or seat.bus_id != viaje.bus_id
    )
    if invalid_ids:
        raise InvalidSeatError(invalid_ids)

    return seats_by_id


def _get_active_fare(*, viaje, origen, destino):
    try:
        return Tarifa.objects.get(
            ruta_id=viaje.ruta_id,
            origen=origen,
            destino=destino,
            activa=True,
        )
    except Tarifa.DoesNotExist as error:
        raise FareNotFoundError(
            "No existe una tarifa activa para el tramo solicitado."
        ) from error


def create_reservation(*, usuario, viaje, origen, destino, pasajeros):
    """Crea atómicamente una reserva valorizada y sus pasajeros y detalles."""
    normalized_passengers, seat_ids = _validate_passenger_requests(pasajeros)

    with transaction.atomic():
        try:
            locked_trip = Viaje.objects.select_for_update(of=("self",)).get(
                pk=viaje.pk
            )
        except (AttributeError, Viaje.DoesNotExist) as error:
            raise TripNotAvailableError("El viaje no está disponible.") from error

        _validate_trip_available(locked_trip)
        validate_segment(
            viaje=locked_trip,
            origen=origen,
            destino=destino,
        )
        fare = _get_active_fare(
            viaje=locked_trip,
            origen=origen,
            destino=destino,
        )
        seats_by_id = _get_valid_seats(
            seat_ids=seat_ids,
            viaje=locked_trip,
        )

        unavailable_ids = (
            _get_unavailable_seat_ids_for_valid_segment(
                viaje=locked_trip,
                origen=origen,
                destino=destino,
            )
            & seat_ids
        )
        if unavailable_ids:
            raise SeatUnavailableError(unavailable_ids)

        reservation = Reserva(
            usuario=usuario,
            viaje=locked_trip,
            origen=origen,
            destino=destino,
            total=fare.precio * len(normalized_passengers),
        )
        reservation.full_clean()
        reservation.save()

        for passenger_data in normalized_passengers:
            seat_id = passenger_data.pop("asiento_id")
            passenger = Pasajero(
                reserva=reservation,
                **passenger_data,
            )
            passenger.full_clean()
            passenger.save()

            detail = DetalleReserva(
                reserva=reservation,
                pasajero=passenger,
                asiento=seats_by_id[seat_id],
                precio_unitario=fare.precio,
            )
            detail.full_clean()
            detail.save()

    return reservation


def pay_reservation(*, reservation_id):
    """Confirma un pago simulado. La reserva es el primer bloqueo compartido.

    Solo se reutiliza un pago PENDIENTE del monto correcto y sin paid_at.
    Las inconsistencias se rechazan; no se reparan datos automáticamente.
    """
    with transaction.atomic():
        reservation = Reserva.objects.select_for_update().get(pk=reservation_id)
        if reservation.estado != Reserva.Estado.PENDIENTE_PAGO:
            raise BookingNotPayableError(status=reservation.estado)
        payment = Pago.objects.select_for_update().filter(reserva=reservation).first()
        if payment is not None and (
            payment.estado != Pago.Estado.PENDIENTE
            or payment.monto != reservation.total
            or payment.paid_at is not None
        ):
            raise BookingNotPayableError(status=reservation.estado)
        if payment is None:
            payment = Pago(reserva=reservation, monto=reservation.total)
        payment.estado = Pago.Estado.APROBADO
        payment.paid_at = timezone.now()
        payment.full_clean()
        payment.save()
        reservation.estado = Reserva.Estado.CONFIRMADA
        reservation.full_clean()
        reservation.save(update_fields=("estado",))
    return reservation


def cancel_reservation(*, reservation_id):
    """Cancela sin alterar asientos: su disponibilidad se deriva del estado.

    Pendiente exige ausencia de pago; confirmada exige APROBADO, monto
    coincidente y paid_at definido. No oculta combinaciones incoherentes.
    """
    with transaction.atomic():
        reservation = Reserva.objects.select_for_update().get(pk=reservation_id)
        if reservation.estado not in BLOCKING_RESERVATION_STATES:
            raise BookingNotCancellableError(status=reservation.estado)
        payment = Pago.objects.select_for_update().filter(reserva=reservation).first()
        if reservation.estado == Reserva.Estado.PENDIENTE_PAGO:
            if payment is not None:
                raise BookingNotCancellableError(status=reservation.estado)
        else:
            if (
                payment is None
                or payment.estado != Pago.Estado.APROBADO
                or payment.monto != reservation.total
                or payment.paid_at is None
            ):
                raise BookingNotCancellableError(status=reservation.estado)
            payment.estado = Pago.Estado.ANULADO
            payment.full_clean()
            payment.save(update_fields=("estado",))
        reservation.estado = Reserva.Estado.CANCELADA
        reservation.cancelled_at = timezone.now()
        reservation.full_clean()
        reservation.save(update_fields=("estado", "cancelled_at"))
    return reservation
