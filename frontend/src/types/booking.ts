import type { NamedResource } from './travel'

export type DocumentType = 'RUT' | 'PASAPORTE' | 'OTRO'
export type BookingStatus = 'PENDIENTE_PAGO' | 'CONFIRMADA' | 'CANCELADA'
export type PaymentStatus = 'PENDIENTE' | 'APROBADO' | 'ANULADO'

export interface PassengerInput {
  seat_id: number
  first_name: string
  last_name: string
  document_type: DocumentType
  document_number: string
}

export interface PassengerFormValue {
  firstName: string
  lastName: string
  documentType: DocumentType | ''
  documentNumber: string
}

export interface BookingInput {
  trip_id: number
  origin_id: number
  destination_id: number
  passengers: PassengerInput[]
}

export interface Payment {
  id: number
  amount: string
  status: PaymentStatus
  paid_at: string | null
}

export interface BookingPassenger {
  id: number
  first_name: string
  last_name: string
  document_type: DocumentType
  document_number: string
  seat: { id: number; number: string }
  price: string
}

export interface Booking {
  id: number
  code: string
  status: BookingStatus
  trip: { id: number }
  origin: NamedResource
  destination: NamedResource
  passengers: BookingPassenger[]
  total: string
  created_at: string
  payment: Payment | null
}

export interface BookingDraft {
  tripId: number
  originId: number
  destinationId: number
  date: string
  seatIds: number[]
  seatNumbers: string[]
  originName: string
  destinationName: string
  routeName: string
  price: string
  departureDatetime: string
  arrivalDatetime: string
}

export interface BookingFlowPassenger {
  firstName: string
  lastName: string
  seatNumber: string
}

export interface BookingFlowRecord {
  id: number
  code: string
  status: BookingStatus
  origin: NamedResource
  destination: NamedResource
  passengers: BookingFlowPassenger[]
  total: string
  payment: Payment | null
}
