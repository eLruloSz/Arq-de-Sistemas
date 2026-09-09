import { useEffect, useState, type FormEvent } from 'react'
import { getBuses } from '../../api/buses'
import { getDrfErrorMessage } from '../../api/errors'
import { getRoutes } from '../../api/routes'
import { createTrip, getTrips, updateTrip } from '../../api/trips'
import { AdminSectionHeader } from '../../components/admin/AdminSectionHeader'
import type { AdminRoute, AdminTrip, Bus, TripInput, TripStatus } from '../../types/admin'
import { formatDateTimeDate, formatTime } from '../../utils/format'

const statuses: Array<[TripStatus, string]> = [['PROGRAMADO', 'Programado'], ['EN_CURSO', 'En curso'], ['FINALIZADO', 'Finalizado'], ['CANCELADO', 'Cancelado']]
const emptyTrip = (): TripInput => ({ route: 0, bus: 0, departure_datetime: '', status: 'PROGRAMADO' })

export function AdminTrips() {
  const [items, setItems] = useState<AdminTrip[]>([])
  const [routes, setRoutes] = useState<AdminRoute[]>([])
  const [buses, setBuses] = useState<Bus[]>([])
  const [form, setForm] = useState<TripInput>(emptyTrip)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { Promise.all([getTrips(), getRoutes(), getBuses()]).then(([trips, routeItems, busItems]) => { setItems(trips); setRoutes(routeItems); setBuses(busItems) }).catch((requestError) => setError(getDrfErrorMessage(requestError, 'No pudimos cargar los viajes.'))).finally(() => setIsLoading(false)) }, [])
  const routeName = (id: number) => routes.find((route) => route.id === id)?.name ?? `Ruta ${id}`
  const busName = (id: number) => { const bus = buses.find((item) => item.id === id); return bus ? `${bus.internal_number} · ${bus.license_plate}` : `Bus ${id}` }
  function openCreate() { setEditingId(null); setForm({ ...emptyTrip(), route: routes[0]?.id ?? 0, bus: buses[0]?.id ?? 0 }); setShowForm(true); setError(''); setMessage('') }
  function openEdit(item: AdminTrip) { setEditingId(item.id); setForm({ route: item.route, bus: item.bus, departure_datetime: item.departure_datetime.slice(0, 16), status: item.status }); setShowForm(true); setError(''); setMessage('') }

  async function submit(event: FormEvent) {
    event.preventDefault(); setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = editingId ? await updateTrip(editingId, form) : await createTrip(form)
      setItems((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setShowForm(false); setMessage(editingId ? 'Viaje actualizado correctamente.' : 'Viaje creado correctamente.')
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos guardar el viaje.')) }
    finally { setIsSaving(false) }
  }

  return <section className="flow-page admin-page">
    <AdminSectionHeader title="Viajes" onCreate={openCreate} />
    {error && <p className="form-message form-message--error" role="alert">{error}</p>}{message && <p className="form-message form-message--success" role="status">{message}</p>}
    {showForm && <form className="admin-form-card" onSubmit={submit}><h2>{editingId ? 'Editar viaje' : 'Crear viaje'}</h2><div className="admin-form-grid">
      <label>Ruta<select required value={form.route || ''} onChange={(event) => setForm({ ...form, route: Number(event.target.value) })}><option value="" disabled>Selecciona una ruta</option>{routes.map((route) => <option key={route.id} value={route.id}>{route.name}</option>)}</select></label>
      <label>Bus<select required value={form.bus || ''} onChange={(event) => setForm({ ...form, bus: Number(event.target.value) })}><option value="" disabled>Selecciona un bus</option>{buses.map((bus) => <option key={bus.id} value={bus.id}>{busName(bus.id)}</option>)}</select></label>
      <label>Fecha/hora de salida<input required type="datetime-local" value={form.departure_datetime} onChange={(event) => setForm({ ...form, departure_datetime: event.target.value })} /></label>
      <label>Estado<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as TripStatus })}>{statuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div><div className="admin-form-actions"><button className="button button--secondary" type="button" onClick={() => setShowForm(false)}>Volver</button><button className="button" disabled={isSaving}>{isSaving ? 'Guardando...' : 'Guardar'}</button></div></form>}
    {isLoading ? <div className="page-status">Cargando viajes...</div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Ruta</th><th>Bus</th><th>Salida</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{routeName(item.route)}</td><td>{busName(item.bus)}</td><td>{formatDateTimeDate(item.departure_datetime)} · {formatTime(item.departure_datetime)}</td><td>{statuses.find(([value]) => value === item.status)?.[1] ?? item.status}</td><td><button className="button button--secondary button--small" type="button" onClick={() => openEdit(item)}>Editar</button></td></tr>)}</tbody></table></div>}
  </section>
}
