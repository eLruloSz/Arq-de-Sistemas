import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { createBooking, payBooking } from '../api/bookings'
import { getDomainError, getFriendlyDomainMessage } from '../api/domainErrors'
import { BookingSummary } from '../components/checkout/BookingSummary'
import { PassengerForm } from '../components/checkout/PassengerForm'
import type {
  BookingDraft,
  BookingFlowRecord,
  DocumentType,
  PassengerFormValue,
} from '../types/booking'
import {
  clearBookingDraft,
  clearPendingBooking,
  getBookingDraft,
  getPendingBooking,
  saveBookingDraft,
  saveConfirmedBooking,
  savePendingBooking,
  toBookingFlowRecord,
} from '../utils/bookingStorage'
import { formatMoney } from '../utils/format'

const emptyPassenger = (): PassengerFormValue => ({
  firstName: '',
  lastName: '',
  documentType: '',
  documentNumber: '',
})

function seatsUrl(draft: BookingDraft) {
  const query = new URLSearchParams({
    origin: String(draft.originId),
    destination: String(draft.destinationId),
    ...(draft.date ? { date: draft.date } : {}),
  })
  return `/trips/${draft.tripId}/seats?${query.toString()}`
}

export function Checkout() {
  const navigate = useNavigate()
  const [draft, setDraft] = useState<BookingDraft | null>(() => getBookingDraft())
  const [pendingBooking, setPendingBooking] = useState<BookingFlowRecord | null>(() => getPendingBooking())
  const [passengers, setPassengers] = useState<PassengerFormValue[]>(() =>
    getBookingDraft()?.seatIds.map(() => emptyPassenger()) ?? [],
  )
  const [isCreating, setIsCreating] = useState(false)
  const [isPaying, setIsPaying] = useState(false)
  const [error, setError] = useState('')

  if (!draft && !pendingBooking) return <Navigate to="/" replace />

  function updatePassenger(index: number, value: PassengerFormValue) {
    setPassengers((current) => current.map((passenger, currentIndex) =>
      currentIndex === index ? value : passenger,
    ))
  }

  async function confirmBooking(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draft) return
    setError('')

    const incomplete = passengers.some((passenger) =>
      !passenger.firstName.trim() ||
      !passenger.lastName.trim() ||
      !passenger.documentType ||
      !passenger.documentNumber.trim(),
    )
    if (incomplete) {
      setError('Completa todos los datos de cada pasajero.')
      return
    }

    setIsCreating(true)
    try {
      const booking = await createBooking({
        trip_id: draft.tripId,
        origin_id: draft.originId,
        destination_id: draft.destinationId,
        passengers: passengers.map((passenger, index) => ({
          seat_id: draft.seatIds[index],
          first_name: passenger.firstName.trim(),
          last_name: passenger.lastName.trim(),
          document_type: passenger.documentType as DocumentType,
          document_number: passenger.documentNumber.trim(),
        })),
      })
      const record = toBookingFlowRecord(booking)
      savePendingBooking(record)
      clearBookingDraft()
      setDraft(null)
      setPendingBooking(record)
      if (booking.status !== 'PENDIENTE_PAGO') {
        setError(`La reserva fue creada con estado ${booking.status}.`)
      }
    } catch (requestError) {
      const domainError = getDomainError(requestError)
      if (domainError?.code === 'SEAT_NOT_AVAILABLE') {
        saveBookingDraft({ ...draft, seatIds: [], seatNumbers: [] })
        navigate(seatsUrl(draft), {
          replace: true,
          state: {
            conflictMessage:
              'Uno o más asientos seleccionados ya no están disponibles. Actualizamos el mapa para que puedas elegir nuevamente.',
          },
        })
        return
      }
      setError(getFriendlyDomainMessage(requestError, 'No pudimos crear la reserva. Revisa los datos e intenta nuevamente.'))
    } finally {
      setIsCreating(false)
    }
  }

  async function pay() {
    if (!pendingBooking) return
    setError('')
    setIsPaying(true)
    try {
      const paidBooking = await payBooking(pendingBooking.id)
      const record = toBookingFlowRecord(paidBooking)
      saveConfirmedBooking(record)
      clearPendingBooking()
      navigate(`/booking-confirmation/${record.id}`, { replace: true })
    } catch (requestError) {
      setError(getFriendlyDomainMessage(requestError, 'No pudimos procesar el pago simulado. Intenta nuevamente.'))
    } finally {
      setIsPaying(false)
    }
  }

  if (pendingBooking) {
    return (
      <section className="flow-page checkout-page">
        <div className="page-heading">
          <div><span className="eyebrow">Pago simulado</span><h1>Reserva pendiente</h1><p>Código: {pendingBooking.code}</p></div>
        </div>
        {error && <p className="form-message form-message--error" role="alert">{error}</p>}
        <div className="checkout-layout">
          <div className="payment-card">
            <h2>Todo listo para confirmar</h2>
            <p>Este proyecto utiliza un pago simulado. No se solicitan datos bancarios ni de tarjetas.</p>
            <div className="payment-status"><span>Estado de la reserva</span><strong>{pendingBooking.status}</strong></div>
            <button className="button button--full" type="button" disabled={isPaying || pendingBooking.status !== 'PENDIENTE_PAGO'} onClick={pay}>
              {isPaying ? 'Procesando pago...' : 'Pagar reserva'}
            </button>
          </div>
          <BookingSummary
            origin={pendingBooking.origin.name}
            destination={pendingBooking.destination.name}
            seatNumbers={pendingBooking.passengers.map((passenger) => passenger.seatNumber)}
            passengerNames={pendingBooking.passengers.map((passenger) => `${passenger.firstName} ${passenger.lastName}`)}
            total={pendingBooking.total}
          />
        </div>
      </section>
    )
  }

  if (!draft) return null
  const estimatedTotal = Number(draft.price) * draft.seatIds.length

  return (
    <section className="flow-page checkout-page">
      <div className="page-heading">
        <div><span className="eyebrow">Datos de pasajeros</span><h1>Completa tu reserva</h1><p>Ingresa los datos correspondientes a cada asiento.</p></div>
        <button className="button button--secondary" type="button" onClick={() => navigate(seatsUrl(draft))}>Cambiar asientos</button>
      </div>
      {error && <p className="form-message form-message--error" role="alert">{error}</p>}
      <form className="checkout-layout" onSubmit={confirmBooking}>
        <div className="passenger-list">
          {draft.seatIds.map((seatId, index) => (
            <PassengerForm
              key={seatId}
              index={index}
              seatNumber={draft.seatNumbers[index]}
              value={passengers[index]}
              onChange={(value) => updatePassenger(index, value)}
            />
          ))}
        </div>
        <div>
          <BookingSummary
            origin={draft.originName}
            destination={draft.destinationName}
            seatNumbers={draft.seatNumbers}
            unitPrice={draft.price}
            total={estimatedTotal}
            departureDatetime={draft.departureDatetime}
            passengerNames={passengers.filter((passenger) => passenger.firstName || passenger.lastName).map((passenger) => `${passenger.firstName} ${passenger.lastName}`.trim())}
          />
          <button className="button button--full confirm-booking-button" type="submit" disabled={isCreating}>
            {isCreating ? 'Creando reserva...' : 'Confirmar reserva'}
          </button>
        </div>
      </form>
      <p className="source-note checkout-note">Total estimado: {formatMoney(estimatedTotal)}. El backend determina el precio final.</p>
    </section>
  )
}
