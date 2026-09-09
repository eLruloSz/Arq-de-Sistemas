import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { cancelBooking, getBooking, payBooking } from '../api/bookings'
import { getFriendlyDomainMessage } from '../api/domainErrors'
import { BookingStatusBadge } from '../components/bookings/BookingStatusBadge'
import type { Booking } from '../types/booking'
import { formatDateTimeDate, formatMoney, formatTime } from '../utils/format'

type BookingAction = 'pay' | 'cancel'

function paymentStatus(booking: Booking) {
  if (booking.payment) return booking.payment.status
  return booking.status === 'PENDIENTE_PAGO' ? 'Pendiente / sin realizar' : 'Sin pago'
}

function isNotFoundError(error: unknown) {
  return axios.isAxiosError(error) && error.response?.status === 404
}

export function BookingDetail() {
  const { id = '' } = useParams()
  const bookingId = Number(id)
  const invalidBookingId = !Number.isInteger(bookingId) || bookingId <= 0
  const [booking, setBooking] = useState<Booking | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [action, setAction] = useState<BookingAction | null>(null)
  const [confirmingCancellation, setConfirmingCancellation] = useState(false)

  useEffect(() => {
    if (invalidBookingId) return

    let active = true
    getBooking(bookingId)
      .then((data) => {
        if (active) setBooking(data)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        if (isNotFoundError(requestError)) {
          setNotFound(true)
        } else {
          setError('No pudimos cargar esta reserva. Intenta nuevamente.')
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [bookingId, invalidBookingId])

  async function pay() {
    if (!booking) return
    setAction('pay')
    setError('')
    setSuccess('')
    try {
      setBooking(await payBooking(booking.id))
      setSuccess('La reserva fue pagada correctamente.')
    } catch (requestError) {
      if (isNotFoundError(requestError)) {
        setNotFound(true)
        return
      }
      setError(getFriendlyDomainMessage(
        requestError,
        'No pudimos pagar esta reserva. Intenta nuevamente.',
      ))
    } finally {
      setAction(null)
    }
  }

  async function cancel() {
    if (!booking) return
    setAction('cancel')
    setError('')
    setSuccess('')
    try {
      setBooking(await cancelBooking(booking.id))
      setConfirmingCancellation(false)
      setSuccess('La reserva fue cancelada correctamente.')
    } catch (requestError) {
      if (isNotFoundError(requestError)) {
        setNotFound(true)
        return
      }
      setError(getFriendlyDomainMessage(
        requestError,
        'No pudimos cancelar esta reserva. Intenta nuevamente.',
      ))
    } finally {
      setAction(null)
    }
  }

  if (invalidBookingId || notFound) {
    return (
      <section className="flow-page empty-state">
        <h1>Reserva no encontrada.</h1>
        <p>No existe o no tienes acceso a esta reserva.</p>
        <Link className="button" to="/bookings">Volver a mis reservas</Link>
      </section>
    )
  }

  if (isLoading) return <div className="page-status" role="status">Cargando reserva...</div>

  if (!booking) {
    return (
      <section className="flow-page empty-state">
        <h1>No pudimos cargar la reserva.</h1>
        <p>{error}</p>
        <Link className="button" to="/bookings">Volver a mis reservas</Link>
      </section>
    )
  }

  const canPay = booking.status === 'PENDIENTE_PAGO'
  const canCancel = booking.status === 'PENDIENTE_PAGO' || booking.status === 'CONFIRMADA'
  const unitPrice = booking.passengers[0]?.price

  return (
    <section className="flow-page booking-detail-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Detalle de reserva</span>
          <h1>{booking.origin.name} <span aria-hidden="true">→</span> {booking.destination.name}</h1>
          <p>Código: {booking.code}</p>
        </div>
        <BookingStatusBadge status={booking.status} />
      </div>

      {error && <p className="form-message form-message--error" role="alert">{error}</p>}
      {success && <p className="form-message form-message--success" role="status">{success}</p>}

      <div className="booking-detail-layout">
        <div className="booking-detail-card">
          <h2>Información de la reserva</h2>
          <dl className="booking-detail-list">
            <div><dt>Estado</dt><dd>{booking.status}</dd></div>
            <div><dt>Reserva creada</dt><dd>{formatDateTimeDate(booking.created_at)} · {formatTime(booking.created_at)}</dd></div>
            <div><dt>Asientos</dt><dd>{booking.passengers.map((passenger) => passenger.seat.number).join(', ')}</dd></div>
            <div><dt>Precio unitario</dt><dd>{unitPrice ? formatMoney(unitPrice) : 'Sin información'}</dd></div>
            <div><dt>Total</dt><dd>{formatMoney(booking.total)}</dd></div>
            <div><dt>Pago</dt><dd>{paymentStatus(booking)}</dd></div>
            {booking.payment && <div><dt>Monto pagado</dt><dd>{formatMoney(booking.payment.amount)}</dd></div>}
          </dl>

          {canCancel && !confirmingCancellation && (
            <div className="booking-actions">
              {canPay && (
                <button className="button" type="button" disabled={action !== null} onClick={pay}>
                  {action === 'pay' ? 'Procesando pago...' : 'Pagar reserva'}
                </button>
              )}
              <button className="button button--secondary" type="button" disabled={action !== null} onClick={() => setConfirmingCancellation(true)}>
                Cancelar reserva
              </button>
            </div>
          )}

          {confirmingCancellation && (
            <div className="cancel-confirmation" role="alertdialog" aria-labelledby="cancel-title">
              <h3 id="cancel-title">¿Deseas cancelar esta reserva?</h3>
              <p>Los asientos volverán a estar disponibles.</p>
              <div className="booking-actions">
                <button className="button button--secondary" type="button" disabled={action !== null} onClick={() => setConfirmingCancellation(false)}>Volver</button>
                <button className="button" type="button" disabled={action !== null} onClick={cancel}>
                  {action === 'cancel' ? 'Cancelando...' : 'Cancelar reserva'}
                </button>
              </div>
            </div>
          )}
        </div>

        <aside className="booking-detail-card">
          <h2>Pasajeros</h2>
          <div className="booking-passengers">
            {booking.passengers.map((passenger) => (
              <div key={passenger.id}>
                <strong>{passenger.first_name} {passenger.last_name}</strong>
                <span>Asiento {passenger.seat.number}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <Link className="booking-back-link" to="/bookings">← Volver a mis reservas</Link>
    </section>
  )
}
