import { Link } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

export function Home() {
  const { isAuthenticated, isAdmin } = useAuth()

  return (
    <div className="home-page">
      <section className="hero-section">
        <div className="hero-copy">
          <span className="eyebrow">Viaja por Chile</span>
          <h1>Tu próximo destino comienza aquí</h1>
          <p>
            Una plataforma sencilla para comprar y gestionar pasajes de buses
            interurbanos de forma segura.
          </p>
          {!isAuthenticated && (
            <div className="hero-actions">
              <Link className="button" to="/register">Crear una cuenta</Link>
              <Link className="button button--secondary" to="/login">Iniciar sesión</Link>
            </div>
          )}
          {isAuthenticated && (
            <Link className="button" to={isAdmin ? '/admin' : '/bookings'}>
              {isAdmin ? 'Ir a administración' : 'Ver mis reservas'}
            </Link>
          )}
        </div>
        <div className="route-illustration" aria-hidden="true">
          <span className="route-line" />
          <span className="route-stop route-stop--start" />
          <span className="route-stop route-stop--middle" />
          <span className="route-stop route-stop--end" />
          <span className="bus-card">BUS</span>
        </div>
      </section>

      <section className="search-preview" aria-labelledby="search-title">
        <div>
          <span className="eyebrow">Próxima funcionalidad</span>
          <h2 id="search-title">Busca tu próximo viaje</h2>
          <p>La búsqueda de rutas y fechas estará disponible en la ETAPA 5B.</p>
        </div>
        <span className="status-pill">Próximamente</span>
      </section>
    </div>
  )
}
