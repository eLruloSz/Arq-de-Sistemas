import { useEffect, useState, type FormEvent } from 'react'
import { getDomainError } from '../../api/domainErrors'
import { getDrfErrorMessage } from '../../api/errors'
import { createRoute, getRoutes, getRouteStops, replaceRouteStops, updateRoute } from '../../api/routes'
import { getStops } from '../../api/stops'
import { AdminSectionHeader } from '../../components/admin/AdminSectionHeader'
import type { AdminRoute, RouteInput, RouteStopInput } from '../../types/admin'
import type { Stop } from '../../types/travel'

const emptyRoute = (): RouteInput => ({ name: '', active: true })

export function AdminRoutes() {
  const [items, setItems] = useState<AdminRoute[]>([])
  const [stops, setStops] = useState<Stop[]>([])
  const [form, setForm] = useState<RouteInput>(emptyRoute)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [selectedRoute, setSelectedRoute] = useState<AdminRoute | null>(null)
  const [routeStops, setRouteStops] = useState<RouteStopInput[]>([])
  const [routeStopLabels, setRouteStopLabels] = useState<Record<number, string>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { Promise.all([getRoutes(), getStops()]).then(([routes, stopItems]) => { setItems(routes); setStops(stopItems) }).catch((requestError) => setError(getDrfErrorMessage(requestError, 'No pudimos cargar las rutas.'))).finally(() => setIsLoading(false)) }, [])
  function openCreate() { setSelectedRoute(null); setEditingId(null); setForm(emptyRoute()); setShowForm(true); setError(''); setMessage('') }
  function openEdit(item: AdminRoute) { setSelectedRoute(null); setEditingId(item.id); setForm({ name: item.name, active: item.active }); setShowForm(true); setError(''); setMessage('') }

  async function submit(event: FormEvent) {
    event.preventDefault(); setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = editingId ? await updateRoute(editingId, form) : await createRoute(form)
      setItems((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setShowForm(false); setMessage(editingId ? 'Ruta actualizada correctamente.' : 'Ruta creada correctamente.')
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos guardar la ruta.')) }
    finally { setIsSaving(false) }
  }

  async function openRouteStops(route: AdminRoute) {
    setShowForm(false); setSelectedRoute(route); setError(''); setMessage('')
    try {
      const current = await getRouteStops(route.id)
      setRouteStops(current.map(({ stop_id, order, minutes_from_origin }) => ({ stop_id, order, minutes_from_origin })))
      setRouteStopLabels(Object.fromEntries(current.map((item) => [item.stop_id, `${item.name} · ${item.city}`])))
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos cargar las paradas de la ruta.')) }
  }

  function updateRouteStop(index: number, changes: Partial<RouteStopInput>) {
    setRouteStops((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...changes } : item))
  }

  async function saveRouteStops() {
    if (!selectedRoute) return
    setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = await replaceRouteStops(selectedRoute.id, routeStops)
      setItems((current) => current.map((item) => item.id === selectedRoute.id ? { ...item, stops: saved } : item))
      setSelectedRoute((current) => current ? { ...current, stops: saved } : null)
      setMessage('Paradas de la ruta guardadas correctamente.')
    } catch (requestError) {
      const domainError = getDomainError(requestError)
      setError(domainError?.code === 'ROUTE_IN_USE' ? 'No es posible modificar las paradas de esta ruta porque ya posee información asociada.' : getDrfErrorMessage(requestError, 'No pudimos guardar las paradas de la ruta.'))
    } finally { setIsSaving(false) }
  }

  const stopLabel = (stopId: number) => { const stop = stops.find((item) => item.id === stopId); return stop ? `${stop.name} · ${stop.city}` : routeStopLabels[stopId] ?? `Parada ${stopId}` }

  return <section className="flow-page admin-page">
    <AdminSectionHeader title="Rutas" onCreate={openCreate} />
    {error && <p className="form-message form-message--error" role="alert">{error}</p>}{message && <p className="form-message form-message--success" role="status">{message}</p>}
    {showForm && <form className="admin-form-card" onSubmit={submit}><h2>{editingId ? 'Editar ruta' : 'Crear ruta'}</h2><div className="admin-form-grid">
      <label>Nombre<input required maxLength={150} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
      <label className="admin-checkbox"><input type="checkbox" checked={form.active} onChange={(event) => setForm({ ...form, active: event.target.checked })} /> Activa</label>
    </div><div className="admin-form-actions"><button className="button button--secondary" type="button" onClick={() => setShowForm(false)}>Volver</button><button className="button" disabled={isSaving}>{isSaving ? 'Guardando...' : 'Guardar'}</button></div></form>}
    {selectedRoute && <div className="admin-form-card"><h2>Paradas · {selectedRoute.name}</h2><div className="admin-table-wrap"><table className="admin-table admin-route-stops"><thead><tr><th>Orden</th><th>Parada</th><th>Minutos desde origen</th><th>Acción</th></tr></thead><tbody>{routeStops.map((item, index) => <tr key={`${index}-${item.stop_id}`}>
      <td><input aria-label={`Orden fila ${index + 1}`} min={0} type="number" value={item.order} onChange={(event) => updateRouteStop(index, { order: Number(event.target.value) })} /></td>
      <td><select aria-label={`Parada fila ${index + 1}`} value={item.stop_id || ''} onChange={(event) => updateRouteStop(index, { stop_id: Number(event.target.value) })}><option value="" disabled>Selecciona una parada</option>{!stops.some((stop) => stop.id === item.stop_id) && item.stop_id > 0 && <option value={item.stop_id}>{stopLabel(item.stop_id)}</option>}{stops.map((stop) => <option key={stop.id} value={stop.id}>{stopLabel(stop.id)}</option>)}</select></td>
      <td><input aria-label={`Minutos fila ${index + 1}`} min={0} type="number" value={item.minutes_from_origin} onChange={(event) => updateRouteStop(index, { minutes_from_origin: Number(event.target.value) })} /></td>
      <td><button className="button button--secondary button--small" type="button" onClick={() => setRouteStops((current) => current.filter((_, itemIndex) => itemIndex !== index))}>Quitar</button></td>
    </tr>)}</tbody></table></div><div className="admin-form-actions admin-form-actions--spread"><button className="button button--secondary" type="button" onClick={() => setRouteStops((current) => [...current, { stop_id: stops[0]?.id ?? 0, order: current.length, minutes_from_origin: 0 }])}>Agregar fila</button><div><button className="button button--secondary" type="button" onClick={() => setSelectedRoute(null)}>Volver</button><button className="button" type="button" disabled={isSaving || routeStops.length < 2 || routeStops.some((item) => !item.stop_id)} onClick={saveRouteStops}>{isSaving ? 'Guardando...' : 'Guardar paradas'}</button></div></div></div>}
    {isLoading ? <div className="page-status">Cargando rutas...</div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Nombre</th><th>Estado</th><th>Paradas ordenadas</th><th>Acciones</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.active ? 'Activa' : 'Inactiva'}</td><td>{item.stops.length ? item.stops.map((stop) => stop.name).join(' → ') : 'Sin configurar'}</td><td><div className="admin-row-actions"><button className="button button--secondary button--small" type="button" onClick={() => openEdit(item)}>Editar</button><button className="button button--secondary button--small" type="button" onClick={() => openRouteStops(item)}>Configurar paradas</button></div></td></tr>)}</tbody></table></div>}
  </section>
}
