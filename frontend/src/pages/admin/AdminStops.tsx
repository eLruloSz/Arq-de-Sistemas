import { useEffect, useState, type FormEvent } from 'react'
import { createStop, getStops, updateStop, type StopInput } from '../../api/stops'
import { getDrfErrorMessage } from '../../api/errors'
import { AdminSectionHeader } from '../../components/admin/AdminSectionHeader'
import type { Stop } from '../../types/travel'

const emptyStop = (): StopInput => ({ name: '', city: '', address: '', active: true })

export function AdminStops() {
  const [items, setItems] = useState<Stop[]>([])
  const [form, setForm] = useState<StopInput>(emptyStop)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { getStops().then(setItems).catch((requestError) => setError(getDrfErrorMessage(requestError, 'No pudimos cargar las paradas.'))).finally(() => setIsLoading(false)) }, [])
  function openCreate() { setEditingId(null); setForm(emptyStop()); setShowForm(true); setError(''); setMessage('') }
  function openEdit(item: Stop) { setEditingId(item.id); setForm({ name: item.name, city: item.city, address: item.address, active: item.active }); setShowForm(true); setError(''); setMessage('') }

  async function submit(event: FormEvent) {
    event.preventDefault(); setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = editingId ? await updateStop(editingId, form) : await createStop(form)
      setItems((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setShowForm(false); setMessage(editingId ? 'Parada actualizada correctamente.' : 'Parada creada correctamente.')
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos guardar la parada.')) }
    finally { setIsSaving(false) }
  }

  return <section className="flow-page admin-page">
    <AdminSectionHeader title="Paradas" onCreate={openCreate} />
    {error && <p className="form-message form-message--error" role="alert">{error}</p>}{message && <p className="form-message form-message--success" role="status">{message}</p>}
    {showForm && <form className="admin-form-card" onSubmit={submit}><h2>{editingId ? 'Editar parada' : 'Crear parada'}</h2><div className="admin-form-grid">
      <label>Nombre<input required maxLength={100} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
      <label>Ciudad<input required maxLength={100} value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} /></label>
      <label className="admin-field--wide">Dirección<input maxLength={255} value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
      <label className="admin-checkbox"><input type="checkbox" checked={form.active} onChange={(event) => setForm({ ...form, active: event.target.checked })} /> Activa</label>
    </div><div className="admin-form-actions"><button className="button button--secondary" type="button" onClick={() => setShowForm(false)}>Volver</button><button className="button" disabled={isSaving}>{isSaving ? 'Guardando...' : 'Guardar'}</button></div></form>}
    {isLoading ? <div className="page-status">Cargando paradas...</div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Nombre</th><th>Ciudad</th><th>Dirección</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.city}</td><td>{item.address || '—'}</td><td>{item.active ? 'Activa' : 'Inactiva'}</td><td><button className="button button--secondary button--small" type="button" onClick={() => openEdit(item)}>Editar</button></td></tr>)}</tbody></table></div>}
  </section>
}
