import type { CSSProperties } from 'react'
import type { Seat } from '../../types/travel'

interface SeatMapProps {
  seats: Seat[]
  selectedIds: number[]
  onToggle: (seat: Seat) => void
}

export function SeatMap({ seats, selectedIds, onToggle }: SeatMapProps) {
  if (seats.length === 0) return <p>No hay asientos configurados para este bus.</p>

  const rows = seats.map((seat) => seat.row)
  const columns = seats.map((seat) => seat.column)
  const minRow = Math.min(...rows)
  const minColumn = Math.min(...columns)
  const columnCount = Math.max(...columns) - minColumn + 1

  return (
    <div className="seat-map-wrapper">
      <div className="bus-front"><span aria-hidden="true">◉</span> Conductor</div>
      <div
        className="seat-grid"
        style={{ '--seat-columns': columnCount } as CSSProperties}
        aria-label="Mapa de asientos"
      >
        {seats.map((seat) => {
          const selected = selectedIds.includes(seat.id)
          const state = !seat.available ? 'Ocupado' : selected ? 'Seleccionado' : 'Disponible'
          return (
            <button
              key={seat.id}
              type="button"
              className={`seat seat--${state.toLowerCase()}`}
              style={{ gridRow: seat.row - minRow + 1, gridColumn: seat.column - minColumn + 1 }}
              disabled={!seat.available}
              aria-pressed={selected}
              aria-label={`Asiento ${seat.number}: ${state}`}
              title={`Asiento ${seat.number}: ${state}`}
              onClick={() => onToggle(seat)}
            >
              <strong>{seat.number}</strong>
              <span>{state}</span>
            </button>
          )
        })}
      </div>
      <div className="seat-legend" aria-label="Leyenda de asientos">
        <span><i className="legend-swatch legend-swatch--available" />Disponible</span>
        <span><i className="legend-swatch legend-swatch--selected" />Seleccionado</span>
        <span><i className="legend-swatch legend-swatch--occupied" />Ocupado</span>
      </div>
    </div>
  )
}
