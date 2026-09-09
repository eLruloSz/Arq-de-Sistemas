import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'nav-link nav-link--active' : 'nav-link'

export function Header() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth()
  const displayName = user?.first_name.trim() || user?.username

  return (
    <header className="site-header">
      <div className="header-inner">
        <NavLink className="brand" to="/" aria-label="Pasajes Interurbanos, inicio">
          <span className="brand-mark" aria-hidden="true">PI</span>
          <span>Pasajes Interurbanos</span>
        </NavLink>
        <nav className="main-nav" aria-label="Navegación principal">
          <NavLink className={navClass} to="/" end>Inicio</NavLink>
          {!isAuthenticated && (
            <>
              <NavLink className={navClass} to="/login">Iniciar sesión</NavLink>
              <NavLink className="button button--small" to="/register">Registrarse</NavLink>
            </>
          )}
          {isAuthenticated && !isAdmin && (
            <NavLink className={navClass} to="/bookings">Mis reservas</NavLink>
          )}
          {isAuthenticated && isAdmin && (
            <NavLink className={navClass} to="/admin">Administración</NavLink>
          )}
          {isAuthenticated && (
            <>
              <span className="user-greeting">Hola, {displayName}</span>
              <button className="button-link" type="button" onClick={logout}>Cerrar sesión</button>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
