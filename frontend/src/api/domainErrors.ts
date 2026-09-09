import axios from 'axios'

export interface DomainError {
  code: string
  message: string
  details: Record<string, unknown>
}

export function getDomainError(error: unknown): DomainError | null {
  if (!axios.isAxiosError(error)) return null
  const data: unknown = error.response?.data
  if (!data || typeof data !== 'object') return null
  const candidate = data as Partial<DomainError>
  if (typeof candidate.code !== 'string' || typeof candidate.message !== 'string') {
    return null
  }
  return {
    code: candidate.code,
    message: candidate.message,
    details:
      candidate.details && typeof candidate.details === 'object'
        ? candidate.details
        : {},
  }
}

const FRIENDLY_MESSAGES: Record<string, string> = {
  INVALID_SEGMENT: 'El tramo seleccionado no es válido para este viaje.',
  TRIP_NOT_AVAILABLE: 'El viaje ya no está disponible para reservar.',
  FARE_NOT_FOUND: 'No existe una tarifa disponible para el tramo seleccionado.',
  INVALID_SEAT: 'Uno de los asientos seleccionados no corresponde a este bus.',
  INVALID_RESERVATION: 'No fue posible validar la reserva con los datos enviados.',
  BOOKING_NOT_PAYABLE: 'Esta reserva ya no se encuentra disponible para pago.',
}

export function getFriendlyDomainMessage(error: unknown, fallback: string) {
  const domainError = getDomainError(error)
  if (!domainError) return fallback
  return FRIENDLY_MESSAGES[domainError.code] ?? domainError.message ?? fallback
}
