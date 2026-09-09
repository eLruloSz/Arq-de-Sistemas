import { Link } from 'react-router-dom'

const sections = [
  ['Buses', '/admin/buses'],
  ['Asientos', '/admin/seats'],
  ['Paradas', '/admin/stops'],
  ['Rutas', '/admin/routes'],
  ['Tarifas', '/admin/fares'],
  ['Viajes', '/admin/trips'],
]

export function AdminHome() {
  return (
    <section className="flow-page admin-page">
      <div className="page-heading">
        <div><span className="eyebrow">Gestión operativa</span><h1>Administración</h1></div>
      </div>
      <nav className="admin-home-grid" aria-label="Módulos administrativos">
        {sections.map(([label, path]) => (
          <Link className="admin-module-card" key={path} to={path}>
            <strong>{label}</strong><span>Gestionar →</span>
          </Link>
        ))}
      </nav>
    </section>
  )
}
