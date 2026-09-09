import { formatDateTimeDate, formatMoney, formatTime } from '../../utils/format'

interface BookingSummaryProps {
  origin: string
  destination: string
  seatNumbers: string[]
  total: string | number
  unitPrice?: string
  departureDatetime?: string
  passengerNames?: string[]
}

export function BookingSummary({
  origin,
  destination,
  seatNumbers,
  total,
  unitPrice,
  departureDatetime,
  passengerNames = [],
}: BookingSummaryProps) {
  return (
    <aside className="booking-summary" aria-labelledby="summary-title">
      <span className="eyebrow">Resumen</span>
      <h2 id="summary-title">{origin} <span aria-hidden="true">→</span> {destination}</h2>
      <dl>
        {departureDatetime && <><dt>Fecha</dt><dd>{formatDateTimeDate(departureDatetime)}</dd><dt>Hora</dt><dd>{formatTime(departureDatetime)}</dd></>}
        <dt>Asientos</dt><dd>{seatNumbers.join(', ')}</dd>
        {passengerNames.length > 0 && <><dt>Pasajeros</dt><dd>{passengerNames.join(', ')}</dd></>}
        {unitPrice && <><dt>Precio unitario</dt><dd>{formatMoney(unitPrice)}</dd></>}
        <dt>Total</dt><dd className="summary-total">{formatMoney(total)}</dd>
      </dl>
    </aside>
  )
}
