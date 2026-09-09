import type { BookingStatus } from '../../types/booking'

const STATUS_LABELS: Record<BookingStatus, string> = {
  PENDIENTE_PAGO: 'Pendiente de pago',
  CONFIRMADA: 'Confirmada',
  CANCELADA: 'Cancelada',
}

export function BookingStatusBadge({ status }: { status: BookingStatus }) {
  return (
    <span className={`booking-status booking-status--${status.toLowerCase()}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}
