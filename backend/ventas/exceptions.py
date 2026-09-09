class ReservationDomainError(Exception):
    """Base para errores de dominio durante la gestión de reservas."""


class InvalidSegmentError(ReservationDomainError):
    """El origen y destino no forman un tramo válido para el viaje."""


class TripNotAvailableError(ReservationDomainError):
    """El viaje no admite nuevas reservas."""


class FareNotFoundError(ReservationDomainError):
    """No existe una tarifa activa para el tramo solicitado."""


class SeatUnavailableError(ReservationDomainError):
    """Uno o más asientos ya están ocupados en el tramo solicitado."""

    def __init__(self, seat_ids):
        self.seat_ids = tuple(sorted(set(seat_ids), key=str))
        super().__init__(
            f"Asientos no disponibles: {', '.join(map(str, self.seat_ids))}"
        )


class InvalidSeatError(ReservationDomainError):
    """Uno o más asientos no existen o no pertenecen al bus del viaje."""

    def __init__(self, seat_ids, message="Uno o más asientos no son válidos."):
        self.seat_ids = tuple(sorted(set(seat_ids), key=str))
        super().__init__(message)


class InvalidReservationError(ReservationDomainError):
    """La solicitud de reserva está incompleta o mal formada."""


class BookingNotPayableError(ReservationDomainError):
    """La reserva o su pago no permiten confirmar un pago simulado."""

    def __init__(self, *, status):
        self.status = status
        super().__init__("The booking cannot be paid in its current state.")


class BookingNotCancellableError(ReservationDomainError):
    """La reserva o su pago no permiten una cancelación coherente."""

    def __init__(self, *, status):
        self.status = status
        super().__init__("The booking cannot be cancelled in its current state.")
