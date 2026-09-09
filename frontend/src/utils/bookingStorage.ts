import type { Booking, BookingDraft, BookingFlowRecord } from '../types/booking'

const DRAFT_KEY = 'booking_draft'
const PENDING_KEY = 'pending_booking'
const CONFIRMED_KEY = 'confirmed_booking'

function readJson(key: string): unknown {
  const value = sessionStorage.getItem(key)
  if (!value) return null
  try {
    return JSON.parse(value) as unknown
  } catch {
    sessionStorage.removeItem(key)
    return null
  }
}

function isNumberArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((item) => Number.isInteger(item) && item > 0)
}

export function getBookingDraft(): BookingDraft | null {
  const value = readJson(DRAFT_KEY)
  if (!value || typeof value !== 'object') return null
  const draft = value as Partial<BookingDraft>
  if (
    !Number.isInteger(draft.tripId) ||
    !Number.isInteger(draft.originId) ||
    !Number.isInteger(draft.destinationId) ||
    !isNumberArray(draft.seatIds) ||
    draft.seatIds.length === 0 ||
    !Array.isArray(draft.seatNumbers) ||
    !draft.seatNumbers.every((number) => typeof number === 'string') ||
    draft.seatNumbers.length !== draft.seatIds.length ||
    typeof draft.date !== 'string' ||
    typeof draft.originName !== 'string' ||
    typeof draft.destinationName !== 'string' ||
    typeof draft.routeName !== 'string' ||
    typeof draft.price !== 'string' ||
    typeof draft.departureDatetime !== 'string' ||
    typeof draft.arrivalDatetime !== 'string'
  ) {
    sessionStorage.removeItem(DRAFT_KEY)
    return null
  }
  return draft as BookingDraft
}

export function saveBookingDraft(draft: BookingDraft) {
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
}

export function clearBookingDraft() {
  sessionStorage.removeItem(DRAFT_KEY)
}

export function toBookingFlowRecord(booking: Booking): BookingFlowRecord {
  return {
    id: booking.id,
    code: booking.code,
    status: booking.status,
    origin: booking.origin,
    destination: booking.destination,
    passengers: booking.passengers.map((passenger) => ({
      firstName: passenger.first_name,
      lastName: passenger.last_name,
      seatNumber: passenger.seat.number,
    })),
    total: booking.total,
    payment: booking.payment,
  }
}

function isFlowRecord(value: unknown): value is BookingFlowRecord {
  if (!value || typeof value !== 'object') return false
  const record = value as Partial<BookingFlowRecord>
  return (
    Number.isInteger(record.id) &&
    typeof record.code === 'string' &&
    typeof record.status === 'string' &&
    typeof record.total === 'string' &&
    record.origin !== undefined &&
    typeof record.origin.name === 'string' &&
    record.destination !== undefined &&
    typeof record.destination.name === 'string' &&
    Array.isArray(record.passengers) &&
    record.passengers.every((passenger) =>
      typeof passenger.firstName === 'string' &&
      typeof passenger.lastName === 'string' &&
      typeof passenger.seatNumber === 'string',
    )
  )
}

function getFlowRecord(key: string) {
  const value = readJson(key)
  return isFlowRecord(value) ? value : null
}

export function savePendingBooking(booking: BookingFlowRecord) {
  sessionStorage.setItem(PENDING_KEY, JSON.stringify(booking))
}

export function getPendingBooking() {
  return getFlowRecord(PENDING_KEY)
}

export function clearPendingBooking() {
  sessionStorage.removeItem(PENDING_KEY)
}

export function saveConfirmedBooking(booking: BookingFlowRecord) {
  sessionStorage.setItem(CONFIRMED_KEY, JSON.stringify(booking))
}

export function getConfirmedBooking() {
  return getFlowRecord(CONFIRMED_KEY)
}
