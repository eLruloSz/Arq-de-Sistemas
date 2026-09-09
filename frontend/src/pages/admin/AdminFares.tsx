import { useEffect, useState, type FormEvent } from 'react'
import { getDrfErrorMessage } from '../../api/errors'
import { createFare, getFares, updateFare } from '../../api/fares'
import { getRoutes } from '../../api/routes'
import { AdminSectionHeader } from '../../components/admin/AdminSectionHeader'
import type { AdminRoute, Fare, FareInput } from '../../types/admin'
import { formatMoney } from '../../utils/format'

const emptyFare = (): FareInput => ({ route: 0, origin: 0, destination: 0, price: '', active: true })

export function AdminFares() {
  const [items, setItems] = useState<Fare[]>([])
  const [routes, setRoutes] = useState<AdminRoute[]>([])
  const [form, setForm] = useState<FareInput>(emptyFare)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { Promise.all([getFares(), getRoutes()]).then(([fares, routeItems]) => { setItems(fares); setRoutes(routeItems) }).catch((requestError) => setError(getDrfErrorMessage(requestError, 'No pudimos cargar las tarifas.'))).finally(() => setIsLoading(false)) }, [])
  const selectedStops = routes.find((route) => route.id === form.route)?.stops ?? []
  const routeName = (id: number) => routes.find((route) => route.id === id)?.name ?? `Ruta ${id}`
  const routeStopName = (routeId: number, routeStopId: number) => routes.find((route) => route.id === routeId)?.stops.find((stop) => stop.route_stop_id === routeStopId)?.name ?? `Parada ${routeStopId}`
  function openCreate() { setEditingId(null); setForm({ ...emptyFare(), route: routes[0]?.id ?? 0 }); setShowForm(true); setError(''); setMessage('') }
  function openEdit(item: Fare) { setEditingId(item.id); setForm({ route: item.route, origin: item.origin, destination: item.destination, price: item.price, active: item.active }); setShowForm(true); setError(''); setMessage('') }
  function selectRoute(routeId: number) { const routeStops = routes.find((route) => route.id === routeId)?.stops ?? []; setForm((current) => ({ ...current, route: routeId, origin: routeStops[0]?.route_stop_id ?? 0, destination: routeStops[1]?.route_stop_id ?? 0 })) }

  async function submit(event: FormEvent) {
    event.preventDefault(); setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = editingId ? await updateFare(editingId, form) : await createFare(form)
      setItems((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setShowForm(false); setMessage(editingId ? 'Tarifa actualizada correctamente.' : 'Tarifa creada correctamente.')
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos guardar la tarifa.')) }
    finally { setIsSaving(false) }
  }

  return <section className="flow-page admin-page">
    <AdminSectionHeader title="Tarifas" onCreate={openCreate} />
    {error && <p className="form-message form-message--error" role="alert">{error}</p>}{message && <p className="form-message form-message--success" role="status">{message}</p>}
    {showForm && <form className="admin-form-card" onSubmit={submit}><h2>{editingId ? 'Editar tarifa' : 'Crear tarifa'}</h2><div className="admin-form-grid">
      <label>Ruta<select required value={form.route || ''} onChange={(event) => selectRoute(Number(event.target.value))}><option value="" disabled>Selecciona una ruta</option>{routes.map((route) => <option key={route.id} value={route.id}>{route.name}</option>)}</select></label>
      <label>Origen<select required value={form.origin || ''} onChange={(event) => setForm({ ...form, origin: Number(event.target.value) })}><option value="" disabled>Selecciona el origen</option>{selectedStops.map((stop) => <option key={stop.route_stop_id} value={stop.route_stop_id}>{stop.order}. {stop.name}</option>)}</select></label>
      <label>Destino<select required value={form.destination || ''} onChange={(event) => setForm({ ...form, destination: Number(event.target.value) })}><option value="" disabled>Selecciona el destino</option>{selectedStops.map((stop) => <option key={stop.route_stop_id} value={stop.route_stop_id}>{stop.order}. {stop.name}</option>)}</select></label>
      <label>Precio<input required min="0.01" step="0.01" type="number" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} /></label>
      <label className="admin-checkbox"><input type="checkbox" checked={form.active} onChange={(event) => setForm({ ...form, active: event.target.checked })} /> Activa</label>
    </div><div className="admin-form-actions"><button className="button button--secondary" type="button" onClick={() => setShowForm(false)}>Volver</button><button className="button" disabled={isSaving || !form.origin || !form.destination}>{isSaving ? 'Guardando...' : 'Guardar'}</button></div></form>}
    {isLoading ? <div className="page-status">Cargando tarifas...</div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Ruta</th><th>Origen</th><th>Destino</th><th>Precio</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{routeName(item.route)}</td><td>{routeStopName(item.route, item.origin)}</td><td>{routeStopName(item.route, item.destination)}</td><td>{formatMoney(item.price)}</td><td>{item.active ? 'Activa' : 'Inactiva'}</td><td><button className="button button--secondary button--small" type="button" onClick={() => openEdit(item)}>Editar</button></td></tr>)}</tbody></table></div>}
  </section>
}
