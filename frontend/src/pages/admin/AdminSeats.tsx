import { useEffect, useState, type FormEvent } from 'react'
import { getBuses } from '../../api/buses'
import { getDrfErrorMessage } from '../../api/errors'
import { createSeat, getSeats, updateSeat } from '../../api/seats'
import { AdminSectionHeader } from '../../components/admin/AdminSectionHeader'
import type { AdminSeat, Bus, SeatInput } from '../../types/admin'

const emptySeat = (): SeatInput => ({ bus: 0, number: '', row: 1, column: 1, active: true })

export function AdminSeats() {
  const [items, setItems] = useState<AdminSeat[]>([])
  const [buses, setBuses] = useState<Bus[]>([])
  const [form, setForm] = useState<SeatInput>(emptySeat)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { Promise.all([getSeats(), getBuses()]).then(([seats, busItems]) => { setItems(seats); setBuses(busItems) }).catch((requestError) => setError(getDrfErrorMessage(requestError, 'No pudimos cargar los asientos.'))).finally(() => setIsLoading(false)) }, [])
  const busName = (id: number) => { const bus = buses.find((item) => item.id === id); return bus ? `${bus.internal_number} · ${bus.license_plate}` : `Bus ${id}` }
  function openCreate() { setEditingId(null); setForm({ ...emptySeat(), bus: buses[0]?.id ?? 0 }); setShowForm(true); setError(''); setMessage('') }
  function openEdit(item: AdminSeat) { setEditingId(item.id); setForm({ bus: item.bus, number: item.number, row: item.row, column: item.column, active: item.active }); setShowForm(true); setError(''); setMessage('') }

  async function submit(event: FormEvent) {
    event.preventDefault(); setIsSaving(true); setError(''); setMessage('')
    try {
      const saved = editingId ? await updateSeat(editingId, form) : await createSeat(form)
      setItems((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setShowForm(false); setMessage(editingId ? 'Asiento actualizado correctamente.' : 'Asiento creado correctamente.')
    } catch (requestError) { setError(getDrfErrorMessage(requestError, 'No pudimos guardar el asiento.')) }
    finally { setIsSaving(false) }
  }

  return <section className="flow-page admin-page">
    <AdminSectionHeader title="Asientos" onCreate={openCreate} />
    {error && <p className="form-message form-message--error" role="alert">{error}</p>}{message && <p className="form-message form-message--success" role="status">{message}</p>}
    {showForm && <form className="admin-form-card" onSubmit={submit}><h2>{editingId ? 'Editar asiento' : 'Crear asiento'}</h2><div className="admin-form-grid">
      <label>Bus<select required value={form.bus || ''} onChange={(event) => setForm({ ...form, bus: Number(event.target.value) })}><option value="" disabled>Selecciona un bus</option>{buses.map((bus) => <option key={bus.id} value={bus.id}>{busName(bus.id)}</option>)}</select></label>
      <label>Número<input required maxLength={10} value={form.number} onChange={(event) => setForm({ ...form, number: event.target.value })} /></label>
      <label>Fila<input required min={1} type="number" value={form.row} onChange={(event) => setForm({ ...form, row: Number(event.target.value) })} /></label>
      <label>Columna<input required min={1} type="number" value={form.column} onChange={(event) => setForm({ ...form, column: Number(event.target.value) })} /></label>
      <label className="admin-checkbox"><input type="checkbox" checked={form.active} onChange={(event) => setForm({ ...form, active: event.target.checked })} /> Activo</label>
    </div><div className="admin-form-actions"><button className="button button--secondary" type="button" onClick={() => setShowForm(false)}>Volver</button><button className="button" disabled={isSaving}>{isSaving ? 'Guardando...' : 'Guardar'}</button></div></form>}
    {isLoading ? <div className="page-status">Cargando asientos...</div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Bus</th><th>Número</th><th>Fila</th><th>Columna</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{busName(item.bus)}</td><td>{item.number}</td><td>{item.row}</td><td>{item.column}</td><td>{item.active ? 'Activo' : 'Inactivo'}</td><td><button className="button button--secondary button--small" type="button" onClick={() => openEdit(item)}>Editar</button></td></tr>)}</tbody></table></div>}
  </section>
}
