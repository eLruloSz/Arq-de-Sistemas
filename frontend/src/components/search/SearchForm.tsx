import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Stop } from '../../types/travel'
import { localToday } from '../../utils/format'

interface SearchFormProps {
  stops: Stop[]
  isLoading: boolean
  loadError: string
  initialOrigin?: string
  initialDestination?: string
  initialDate?: string
}

export function SearchForm({
  stops,
  isLoading,
  loadError,
  initialOrigin = '',
  initialDestination = '',
  initialDate = '',
}: SearchFormProps) {
  const navigate = useNavigate()
  const [origin, setOrigin] = useState(initialOrigin)
  const [destination, setDestination] = useState(initialDestination)
  const [date, setDate] = useState(initialDate)
  const [validationError, setValidationError] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError('')
    if (!origin || !destination || !date) {
      setValidationError('Completa origen, destino y fecha.')
      return
    }
    if (origin === destination) {
      setValidationError('El origen y el destino deben ser diferentes.')
      return
    }
    const query = new URLSearchParams({ origin, destination, date })
    navigate(`/trips?${query.toString()}`)
  }

  const stopLabel = (stop: Stop) =>
    stop.name === stop.city ? stop.name : `${stop.name} — ${stop.city}`

  return (
    <form className="search-form" onSubmit={submit}>
      <div className="search-heading">
        <div>
          <span className="eyebrow">Encuentra tu ruta</span>
          <h2>Busca tu próximo viaje</h2>
        </div>
        {isLoading && <span className="loading-note" role="status">Cargando destinos...</span>}
      </div>

      {loadError && <p className="form-message form-message--error" role="alert">{loadError}</p>}
      {validationError && (
        <p className="form-message form-message--error" role="alert">{validationError}</p>
      )}

      <div className="search-fields">
        <div className="form-field">
          <label htmlFor="search-origin">Origen</label>
          <select id="search-origin" required value={origin} onChange={(event) => setOrigin(event.target.value)} disabled={isLoading}>
            <option value="">Selecciona origen</option>
            {stops.map((stop) => <option key={stop.id} value={stop.id}>{stopLabel(stop)}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="search-destination">Destino</label>
          <select id="search-destination" required value={destination} onChange={(event) => setDestination(event.target.value)} disabled={isLoading}>
            <option value="">Selecciona destino</option>
            {stops.map((stop) => <option key={stop.id} value={stop.id}>{stopLabel(stop)}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="search-date">Fecha</label>
          <input id="search-date" type="date" required min={localToday()} value={date} onChange={(event) => setDate(event.target.value)} />
        </div>
        <button className="button search-button" type="submit" disabled={isLoading || stops.length === 0}>
          Buscar viajes
        </button>
      </div>
    </form>
  )
}
