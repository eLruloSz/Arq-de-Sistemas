import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { getApiErrorMessage } from '../api/errors'
import { useAuth } from '../context/useAuth'
import { getBookingDraft } from '../utils/bookingStorage'

interface LoginLocationState {
  registrationSuccess?: boolean
  from?: unknown
}

function getProtectedDestination(from: unknown) {
  if (!from || typeof from !== 'object') return null

  const location = from as { pathname?: unknown; search?: unknown; hash?: unknown }
  if (typeof location.pathname !== 'string') return null

  const isProtectedDestination =
    location.pathname === '/checkout' ||
    location.pathname === '/bookings' ||
    location.pathname === '/admin' ||
    /^\/booking-confirmation\/[^/]+$/.test(location.pathname)

  if (!isProtectedDestination) return null

  const search = typeof location.search === 'string' && location.search.startsWith('?')
    ? location.search
    : ''
  const hash = typeof location.hash === 'string' && location.hash.startsWith('#')
    ? location.hash
    : ''
  return `${location.pathname}${search}${hash}`
}

export function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const locationState = location.state as LoginLocationState | null
  const registrationSuccess = Boolean(locationState?.registrationSuccess)
  const destination =
    getProtectedDestination(locationState?.from) ?? (getBookingDraft() ? '/checkout' : '/')

  if (isAuthenticated) return <Navigate to={destination} replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login({ username, password })
      navigate(destination, { replace: true })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No fue posible iniciar sesión. Intenta nuevamente.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-page" aria-labelledby="login-title">
      <div className="form-card">
        <span className="eyebrow">Bienvenido de vuelta</span>
        <h1 id="login-title">Iniciar sesión</h1>
        <p className="form-intro">Accede para gestionar tus próximos viajes.</p>
        {registrationSuccess && (
          <p className="form-message form-message--success" role="status">
            Tu cuenta fue creada correctamente. Ya puedes iniciar sesión.
          </p>
        )}
        {error && <p className="form-message form-message--error" role="alert">{error}</p>}

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <button className="button button--full" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Cargando...' : 'Iniciar sesión'}
          </button>
        </form>
        <p className="form-switch">
          ¿Aún no tienes cuenta? <Link to="/register">Regístrate</Link>
        </p>
      </div>
    </section>
  )
}
