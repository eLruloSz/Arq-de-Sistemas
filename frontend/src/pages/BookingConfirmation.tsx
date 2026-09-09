import { Link, Navigate, useParams } from 'react-router-dom'
import { BookingSummary } from '../components/checkout/BookingSummary'
import { getConfirmedBooking } from '../utils/bookingStorage'

export function BookingConfirmation() {
  const { id } = useParams()
  const booking = getConfirmedBooking()
  if (!booking || String(booking.id) !== id) return <Navigate to="/" replace />

  return (
    <section className="flow-page confirmation-page">
      <div className="confirmation-banner">
        <span className="confirmation-check" aria-hidden="true">✓</span>
        <span className="eyebrow">Pago aprobado</span>
        <h1>Reserva confirmada</h1>
        <p>Tu compra fue procesada correctamente.</p>
      </div>
      <div className="confirmation-content">
        <div className="confirmation-details">
          <h2>Detalle de la reserva</h2>
          <dl>
            <dt>Código</dt><dd>{booking.code}</dd>
            <dt>Estado</dt><dd>{booking.status}</dd>
            <dt>Estado del pago</dt><dd>{booking.payment?.status ?? 'Sin información'}</dd>
          </dl>
          <div className="confirmation-actions">
            <Link className="button" to="/bookings">Ver mis reservas</Link>
            <Link className="button button--secondary" to="/">Volver al inicio</Link>
          </div>
        </div>
        <BookingSummary
          origin={booking.origin.name}
          destination={booking.destination.name}
          seatNumbers={booking.passengers.map((passenger) => passenger.seatNumber)}
          passengerNames={booking.passengers.map((passenger) => `${passenger.firstName} ${passenger.lastName}`)}
          total={booking.total}
        />
      </div>
    </section>
  )
}
