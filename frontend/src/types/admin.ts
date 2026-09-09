import type { PaginatedResponse, Stop } from './travel'

export type { PaginatedResponse, Stop }

export interface Bus {
  id: number
  license_plate: string
  internal_number: string
  brand: string
  model: string
  active: boolean
  created_at: string
}

export type BusInput = Omit<Bus, 'id' | 'created_at'>

export interface AdminSeat {
  id: number
  bus: number
  number: string
  row: number
  column: number
  active: boolean
}

export type SeatInput = Omit<AdminSeat, 'id'>

export interface RouteStop {
  route_stop_id: number
  stop_id: number
  name: string
  city: string
  order: number
  minutes_from_origin: number
}

export interface RouteStopInput {
  stop_id: number
  order: number
  minutes_from_origin: number
}

export interface AdminRoute {
  id: number
  name: string
  active: boolean
  created_at: string
  stops: RouteStop[]
}

export type RouteInput = Pick<AdminRoute, 'name' | 'active'>

export interface Fare {
  id: number
  route: number
  origin: number
  destination: number
  price: string
  active: boolean
}

export type FareInput = Omit<Fare, 'id'>

export type TripStatus = 'PROGRAMADO' | 'EN_CURSO' | 'FINALIZADO' | 'CANCELADO'

export interface AdminTrip {
  id: number
  route: number
  bus: number
  departure_datetime: string
  status: TripStatus
  created_at: string
}

export type TripInput = Omit<AdminTrip, 'id' | 'created_at'>
