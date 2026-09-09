import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { getApiErrorMessage } from '../api/errors'
import { useAuth } from '../context/useAuth'

interface RegisterForm {
  username: string
  email: string
  firstName: string
  lastName: string
  password: string
  confirmPassword: string
}

const initialForm: RegisterForm = {
  username: '',
  email: '',
  firstName: '',
  lastName: '',
  password: '',
  confirmPassword: '',
}

export function Register() {
  const navigate = useNavigate()
  const { register, isAuthenticated } = useAuth()
  const [form, setForm] = useState(initialForm)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (isAuthenticated) return <Navigate to="/" replace />

  function updateField(field: keyof RegisterForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setIsSubmitting(true)
    try {
      await register({
        username: form.username.trim(),
        email: form.email.trim(),
        first_name: form.firstName.trim(),
        last_name: form.lastName.trim(),
        password: form.password,
      })
      navigate('/login', { replace: true, state: { registrationSuccess: true } })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No fue posible crear la cuenta. Revisa los datos.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-page" aria-labelledby="register-title">
      <div className="form-card form-card--wide">
        <span className="eyebrow">Comienza a viajar</span>
        <h1 id="register-title">Crear una cuenta</h1>
        <p className="form-intro">Regístrate para comprar y gestionar tus pasajes.</p>
        {error && <p className="form-message form-message--error" role="alert">{error}</p>}

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="register-username">Username</label>
              <input id="register-username" autoComplete="username" required value={form.username} onChange={(event) => updateField('username', event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" autoComplete="email" required value={form.email} onChange={(event) => updateField('email', event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="first-name">Nombre</label>
              <input id="first-name" autoComplete="given-name" value={form.firstName} onChange={(event) => updateField('firstName', event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="last-name">Apellido</label>
              <input id="last-name" autoComplete="family-name" value={form.lastName} onChange={(event) => updateField('lastName', event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="register-password">Contraseña</label>
              <input id="register-password" type="password" autoComplete="new-password" minLength={8} required value={form.password} onChange={(event) => updateField('password', event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="confirm-password">Confirmar contraseña</label>
              <input id="confirm-password" type="password" autoComplete="new-password" minLength={8} required value={form.confirmPassword} onChange={(event) => updateField('confirmPassword', event.target.value)} />
            </div>
          </div>
          <button className="button button--full" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Cargando...' : 'Registrarse'}
          </button>
        </form>
        <p className="form-switch">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </div>
    </section>
  )
}
