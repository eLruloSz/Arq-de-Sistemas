import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getBookings } from '../api/bookings'
import { BookingStatusBadge } from '../components/bookings/BookingStatusBadge'
import type { Booking } from '../types/booking'
import { formatDateTimeDate, formatMoney, formatTime } from '../utils/format'

export function Bookings() {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    getBookings()
      .then((data) => {
        if (active) setBookings(data)
      })
      .catch(() => {
        if (active) setError('No pudimos cargar tus reservas. Intenta nuevamente.')
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  if (isLoading) return <div className="page-status" role="status">Cargando reservas...</div>

  return (
    <section className="flow-page bookings-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Área del pasajero</span>
          <h1>Mis reservas</h1>
          <p>Consulta el estado y detalle de tus viajes.</p>
        </div>
      </div>

      {error && <p className="form-message form-message--error" role="alert">{error}</p>}

      {!error && bookings.length === 0 && (
        <div className="empty-state empty-state--card">
          <h2>Aún no tienes reservas.</h2>
          <Link className="button" to="/">Buscar viajes</Link>
        </div>
      )}

      {!error && bookings.length > 0 && (
        <div className="booking-list">
          {bookings.map((booking) => (
            <article className="booking-card" key={booking.id}>
              <div className="booking-card__route">
                <BookingStatusBadge status={booking.status} />
                <h2>{booking.origin.name} <span aria-hidden="true">→</span> {booking.destination.name}</h2>
                <p>Reserva creada: {formatDateTimeDate(booking.created_at)} · {formatTime(booking.created_at)}</p>
              </div>
              <dl className="booking-card__summary">
                <div><dt>Asientos</dt><dd>{booking.passengers.map((passenger) => passenger.seat.number).join(', ')}</dd></div>
                <div><dt>Total</dt><dd>{formatMoney(booking.total)}</dd></div>
              </dl>
              <Link className="button button--secondary" to={`/bookings/${booking.id}`}>Ver detalle</Link>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
