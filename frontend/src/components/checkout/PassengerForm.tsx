import type { PassengerFormValue } from '../../types/booking'

interface PassengerFormProps {
  index: number
  seatNumber: string
  value: PassengerFormValue
  onChange: (value: PassengerFormValue) => void
}

export function PassengerForm({ index, seatNumber, value, onChange }: PassengerFormProps) {
  const prefix = `passenger-${index}`
  const update = (field: keyof PassengerFormValue, fieldValue: string) =>
    onChange({ ...value, [field]: fieldValue })

  return (
    <fieldset className="passenger-card">
      <legend>Pasajero {index + 1} — Asiento {seatNumber}</legend>
      <div className="passenger-grid">
        <div className="form-field">
          <label htmlFor={`${prefix}-first-name`}>Nombre</label>
          <input id={`${prefix}-first-name`} required value={value.firstName} onChange={(event) => update('firstName', event.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor={`${prefix}-last-name`}>Apellido</label>
          <input id={`${prefix}-last-name`} required value={value.lastName} onChange={(event) => update('lastName', event.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor={`${prefix}-document-type`}>Tipo de documento</label>
          <select id={`${prefix}-document-type`} required value={value.documentType} onChange={(event) => update('documentType', event.target.value)}>
            <option value="">Selecciona tipo</option>
            <option value="RUT">RUT</option>
            <option value="PASAPORTE">Pasaporte</option>
            <option value="OTRO">Otro</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor={`${prefix}-document-number`}>Documento</label>
          <input id={`${prefix}-document-number`} required maxLength={30} value={value.documentNumber} onChange={(event) => update('documentNumber', event.target.value)} />
        </div>
      </div>
    </fieldset>
  )
}
