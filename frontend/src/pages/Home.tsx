import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getStops } from '../api/stops'
import { SearchForm } from '../components/search/SearchForm'
import type { Stop } from '../types/travel'

export function Home() {
  const [searchParams] = useSearchParams()
  const [stops, setStops] = useState<Stop[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getStops()
      .then((data) => {
        if (active) {
          setStops(data)
          if (data.length === 0) {
            setError('No hay destinos activos disponibles en este momento.')
          }
        }
      })
      .catch(() => {
        if (active) setError('No pudimos cargar los destinos. Intenta nuevamente más tarde.')
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="home-page">
      <section className="hero-section hero-section--search">
        <div className="hero-copy">
          <span className="eyebrow">Viaja por Chile</span>
          <h1>Tu próximo destino comienza aquí</h1>
          <p>
            Busca rutas, compara horarios y reserva tus asientos de buses
            interurbanos de forma segura.
          </p>
        </div>
        <div className="route-illustration" aria-hidden="true">
          <span className="route-line" />
          <span className="route-stop route-stop--start" />
          <span className="route-stop route-stop--middle" />
          <span className="route-stop route-stop--end" />
          <span className="bus-card">BUS</span>
        </div>
      </section>

      <SearchForm
        stops={stops}
        isLoading={isLoading}
        loadError={error}
        initialOrigin={searchParams.get('origin') ?? ''}
        initialDestination={searchParams.get('destination') ?? ''}
        initialDate={searchParams.get('date') ?? ''}
      />
    </div>
  )
}
