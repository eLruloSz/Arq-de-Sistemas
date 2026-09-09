import { Link } from 'react-router-dom'
import type { TripSearchResult } from '../../types/travel'
import { formatDateTimeDate, formatMoney, formatTime } from '../../utils/format'

interface TripCardProps {
  trip: TripSearchResult
  query: string
}

export function TripCard({ trip, query }: TripCardProps) {
  const selectionUrl = `/trips/${trip.trip_id}/seats?${query}`

  return (
    <article className="trip-card">
      <div className="trip-route">
        <span className="eyebrow">{trip.route.name}</span>
        <h2>{trip.origin.name} <span aria-hidden="true">→</span> {trip.destination.name}</h2>
        <p>{formatDateTimeDate(trip.departure_datetime)}</p>
      </div>
      <div className="trip-times">
        <div><span>Salida</span><strong>{formatTime(trip.departure_datetime)}</strong></div>
        <div className="trip-duration-line" aria-hidden="true" />
        <div><span>Llegada</span><strong>{formatTime(trip.arrival_datetime)}</strong></div>
      </div>
      <div className="trip-purchase">
        <strong className="trip-price">{formatMoney(trip.price)}</strong>
        <span>{trip.available_seats} {trip.available_seats === 1 ? 'asiento disponible' : 'asientos disponibles'}</span>
        {trip.available_seats > 0 ? (
          <Link className="button" to={selectionUrl} state={{ trip }}>Seleccionar</Link>
        ) : (
          <button className="button" type="button" disabled>Sin disponibilidad</button>
        )}
      </div>
    </article>
  )
}
