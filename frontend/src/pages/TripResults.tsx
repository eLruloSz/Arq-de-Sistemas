import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getFriendlyDomainMessage } from '../api/domainErrors'
import { searchTrips } from '../api/trips'
import { TripCard } from '../components/trips/TripCard'
import type { TripSearchResult } from '../types/travel'
import { formatSearchDate } from '../utils/format'

export function TripResults() {
  const [searchParams] = useSearchParams()
  const originValue = searchParams.get('origin') ?? ''
  const destinationValue = searchParams.get('destination') ?? ''
  const date = searchParams.get('date') ?? ''
  const origin = Number(originValue)
  const destination = Number(destinationValue)
  const validQuery =
    Number.isInteger(origin) && origin > 0 &&
    Number.isInteger(destination) && destination > 0 &&
    origin !== destination && /^\d{4}-\d{2}-\d{2}$/.test(date)

  const [trips, setTrips] = useState<TripSearchResult[]>([])
  const [loadedQuery, setLoadedQuery] = useState('')
  const [error, setError] = useState('')
  const query = new URLSearchParams({ origin: originValue, destination: destinationValue, date }).toString()
  const editUrl = `/?${query}`

  useEffect(() => {
    if (!validQuery) return
    let active = true
    searchTrips({ origin, destination, date })
      .then((data) => {
        if (active) {
          setTrips(data)
          setError('')
          setLoadedQuery(query)
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(getFriendlyDomainMessage(requestError, 'No pudimos buscar viajes. Intenta nuevamente.'))
          setLoadedQuery(query)
        }
      })
    return () => {
      active = false
    }
  }, [date, destination, origin, query, validQuery])

  const isLoading = validQuery && loadedQuery !== query
  const visibleError = loadedQuery === query ? error : ''

  if (!validQuery) {
    return (
      <section className="flow-page empty-state">
        <h1>Búsqueda incompleta</h1>
        <p>Selecciona un origen, un destino diferente y una fecha válida.</p>
        <Link className="button" to="/">Volver a buscar</Link>
      </section>
    )
  }

  return (
    <section className="flow-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Resultados</span>
          <h1>Viajes disponibles</h1>
          <p>{formatSearchDate(date)}</p>
        </div>
        <Link className="button button--secondary" to={editUrl}>Modificar búsqueda</Link>
      </div>

      {isLoading && <div className="page-status" role="status">Buscando viajes...</div>}
      {visibleError && <p className="form-message form-message--error" role="alert">{visibleError}</p>}
      {!isLoading && !visibleError && trips.length === 0 && (
        <div className="empty-state empty-state--card">
          <h2>No encontramos viajes para la fecha seleccionada.</h2>
          <p>Prueba otra fecha o modifica el origen y el destino.</p>
          <Link className="button" to={editUrl}>Modificar búsqueda</Link>
        </div>
      )}
      {!isLoading && !visibleError && trips.length > 0 && (
        <div className="trip-list">
          {trips.map((trip) => <TripCard key={trip.trip_id} trip={trip} query={query} />)}
        </div>
      )}
    </section>
  )
}
