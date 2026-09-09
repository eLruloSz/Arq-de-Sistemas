import { Link } from 'react-router-dom'

interface AdminSectionHeaderProps {
  title: string
  onCreate?: () => void
}

export function AdminSectionHeader({ title, onCreate }: AdminSectionHeaderProps) {
  return (
    <div className="page-heading admin-section-heading">
      <div>
        <Link className="admin-back-link" to="/admin">← Administración</Link>
        <h1>{title}</h1>
      </div>
      {onCreate && <button className="button" type="button" onClick={onCreate}>Crear</button>}
    </div>
  )
}
