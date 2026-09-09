import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getFriendlyDomainMessage } from '../api/domainErrors'
import { getTripAvailability, searchTrips } from '../api/trips'
import { SeatMap } from '../components/seats/SeatMap'
import { useAuth } from '../context/useAuth'
import type { Availability, Seat, TripSearchResult } from '../types/travel'
import { getBookingDraft, saveBookingDraft } from '../utils/bookingStorage'
import { formatMoney } from '../utils/format'

interface SeatLocationState {
  trip?: TripSearchResult
  conflictMessage?: string
}

export function SeatSelection() {
  const { tripId: tripIdValue = '' } = useParams()
  const [searchParams] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const tripId = Number(tripIdValue)
  const origin = Number(searchParams.get('origin'))
  const destination = Number(searchParams.get('destination'))
  const date = searchParams.get('date') ?? ''
  const validQuery = Number.isInteger(tripId) && tripId > 0 && Number.isInteger(origin) && origin > 0 && Number.isInteger(destination) && destination > 0 && origin !== destination
  const locationState = location.state as SeatLocationState | null

  const [availability, setAvailability] = useState<Availability | null>(null)
  const [trip, setTrip] = useState<TripSearchResult | null>(locationState?.trip ?? null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [loadedQuery, setLoadedQuery] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState(locationState?.conflictMessage ?? '')

  const query = new URLSearchParams({
    origin: String(origin),
    destination: String(destination),
    ...(date ? { date } : {}),
  }).toString()

  useEffect(() => {
    if (!validQuery) return
    let active = true
    const tripLookup = date
      ? searchTrips({ origin, destination, date })
      : Promise.resolve([])

    Promise.all([getTripAvailability(tripId, origin, destination), tripLookup])
      .then(([availabilityData, matchingTrips]) => {
        if (!active) return
        setAvailability(availabilityData)
        setError('')
        setLoadedQuery(query)
        setTrip((current) => current ?? matchingTrips.find((item) => item.trip_id === tripId) ?? null)
        const draft = getBookingDraft()
        if (draft?.tripId === tripId && draft.originId === origin && draft.destinationId === destination) {
          const availableIds = new Set(availabilityData.seats.filter((seat) => seat.available).map((seat) => seat.id))
          const restored = draft.seatIds.filter((seatId) => availableIds.has(seatId))
          setSelectedIds(restored)
          if (restored.length !== draft.seatIds.length) {
            setNotice('Algunos asientos guardados ya no están disponibles. Actualizamos tu selección.')
          }
        } else {
          setSelectedIds([])
          setNotice(locationState?.conflictMessage ?? '')
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(getFriendlyDomainMessage(requestError, 'No pudimos cargar los asientos.'))
          setLoadedQuery(query)
        }
      })

    return () => {
      active = false
    }
  }, [date, destination, locationState?.conflictMessage, origin, query, tripId, validQuery])

  function toggleSeat(seat: Seat) {
    if (!seat.available) return
    setSelectedIds((current) =>
      current.includes(seat.id)
        ? current.filter((seatId) => seatId !== seat.id)
        : [...current, seat.id],
    )
  }

  function continueToCheckout() {
    if (!availability || selectedIds.length === 0) return
    const selectedSeats = availability.seats.filter((seat) => selectedIds.includes(seat.id))
    saveBookingDraft({
      tripId,
      originId: origin,
      destinationId: destination,
      date,
      seatIds: selectedSeats.map((seat) => seat.id),
      seatNumbers: selectedSeats.map((seat) => seat.number),
      originName: availability.origin.name,
      destinationName: availability.destination.name,
      routeName: trip?.route.name ?? '',
      price: availability.price,
      departureDatetime: trip?.departure_datetime ?? '',
      arrivalDatetime: trip?.arrival_datetime ?? '',
    })

    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: '/checkout' } } })
      return
    }
    navigate('/checkout')
  }

  if (!validQuery) {
    return (
      <section className="flow-page empty-state">
        <h1>Selección no disponible</h1>
        <p>Faltan datos válidos del viaje o del tramo.</p>
        <Link className="button" to="/">Volver al inicio</Link>
      </section>
    )
  }

  const selectedSeats = availability?.seats.filter((seat) => selectedIds.includes(seat.id)) ?? []
  const estimatedTotal = Number(availability?.price ?? 0) * selectedIds.length
  const isLoading = validQuery && loadedQuery !== query
  const visibleError = loadedQuery === query ? error : ''

  return (
    <section className="flow-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Selecciona tus asientos</span>
          <h1>{availability ? `${availability.origin.name} → ${availability.destination.name}` : 'Mapa del bus'}</h1>
          {trip?.route.name && <p>{trip.route.name}</p>}
        </div>
        <Link className="button button--secondary" to={`/trips?${query}`}>Volver a resultados</Link>
      </div>

      {notice && <p className="form-message form-message--warning" role="status">{notice}</p>}
      {isLoading && <div className="page-status" role="status">Cargando asientos...</div>}
      {visibleError && <p className="form-message form-message--error" role="alert">{visibleError}</p>}
      {availability && !isLoading && !visibleError && (
        <div className="seat-layout">
          <div className="seat-map-card">
            <SeatMap seats={availability.seats} selectedIds={selectedIds} onToggle={toggleSeat} />
          </div>
          <aside className="selection-panel">
            <span className="eyebrow">Tu selección</span>
            <h2>{selectedIds.length} {selectedIds.length === 1 ? 'asiento seleccionado' : 'asientos seleccionados'}</h2>
            <p>{selectedSeats.length > 0 ? selectedSeats.map((seat) => seat.number).join(', ') : 'Selecciona al menos un asiento disponible.'}</p>
            <dl><dt>Precio por asiento</dt><dd>{formatMoney(availability.price)}</dd><dt>Total estimado</dt><dd>{formatMoney(estimatedTotal)}</dd></dl>
            <p className="source-note">El precio final será validado por el backend.</p>
            <button className="button button--full" type="button" disabled={selectedIds.length === 0} onClick={continueToCheckout}>Continuar</button>
          </aside>
        </div>
      )}
    </section>
  )
}
