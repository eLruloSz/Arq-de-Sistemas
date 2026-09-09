import { useEffect, useState, type FormEvent } from 'react'
import { createBus, getBuses, updateBus } from '../../api/buses'
import { getDrfErrorMessage } from '../../api/errors'
import { AdminSectionHeader } from '../../components/admin/AdminSectionHeader'
import type { Bus, BusInput } from '../../types/admin'

const emptyBus = (): BusInput => ({ license_plate: '', internal_number: '', brand: '', model: '', active: true })

export function AdminBuses() {
  const [items, setItems] = useState<Bus[]>([])
  const [form, setForm] = useState<BusInput>(emptyBus)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    getBuses().then(setItems).catch((requestError) => setError(getDrfErrorMessage(requestError, 'No pudimos cargar los buses.'))).finally(() => setIsLoading(false))
  }, [])

  function openCreate() { setEditingId(null); setForm(emptyBus()); setShowForm(true); setError(''); setMessage('') }
  function openEdit(item: Bus) { setEditingId(item.id); setForm({ license_plate: item.license_plate, internal_number: item.internal_number, brand: item.brand, model: item.model, active: item.active }); setShowForm(true); setError(''); setMessage('') }

  async function submit(event: FormEvent) {
    event.preventDefault(); setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = editingId ? await updateBus(editingId, form) : await createBus(form)
      setItems((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setShowForm(false); setMessage(editingId ? 'Bus actualizado correctamente.' : 'Bus creado correctamente.')
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos guardar el bus.')) }
    finally { setIsSaving(false) }
  }

  return (
    <section className="flow-page admin-page">
      <AdminSectionHeader title="Buses" onCreate={openCreate} />
      {error && <p className="form-message form-message--error" role="alert">{error}</p>}
      {message && <p className="form-message form-message--success" role="status">{message}</p>}
      {showForm && <form className="admin-form-card" onSubmit={submit}>
        <h2>{editingId ? 'Editar bus' : 'Crear bus'}</h2>
        <div className="admin-form-grid">
          <label>Patente<input required maxLength={10} value={form.license_plate} onChange={(event) => setForm({ ...form, license_plate: event.target.value })} /></label>
          <label>Número interno<input required maxLength={20} value={form.internal_number} onChange={(event) => setForm({ ...form, internal_number: event.target.value })} /></label>
          <label>Marca<input maxLength={50} value={form.brand} onChange={(event) => setForm({ ...form, brand: event.target.value })} /></label>
          <label>Modelo<input maxLength={50} value={form.model} onChange={(event) => setForm({ ...form, model: event.target.value })} /></label>
          <label className="admin-checkbox"><input type="checkbox" checked={form.active} onChange={(event) => setForm({ ...form, active: event.target.checked })} /> Activo</label>
        </div>
        <div className="admin-form-actions"><button className="button button--secondary" type="button" onClick={() => setShowForm(false)}>Volver</button><button className="button" disabled={isSaving}>{isSaving ? 'Guardando...' : 'Guardar'}</button></div>
      </form>}
      {isLoading ? <div className="page-status">Cargando buses...</div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Patente</th><th>Número interno</th><th>Marca</th><th>Modelo</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.license_plate}</td><td>{item.internal_number}</td><td>{item.brand || '—'}</td><td>{item.model || '—'}</td><td>{item.active ? 'Activo' : 'Inactivo'}</td><td><button className="button button--secondary button--small" type="button" onClick={() => openEdit(item)}>Editar</button></td></tr>)}</tbody></table></div>}
    </section>
  )
}
