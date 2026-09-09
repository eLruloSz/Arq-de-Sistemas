export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Stop {
  id: number
  name: string
  city: string
  address: string
  active: boolean
}

export interface NamedResource {
  id: number
  name: string
}

export interface TripSearchParams {
  origin: number
  destination: number
  date: string
}

export interface TripSearchResult {
  trip_id: number
  route: NamedResource
  origin: NamedResource
  destination: NamedResource
  departure_datetime: string
  arrival_datetime: string
  price: string
  available_seats: number
}

export interface Seat {
  id: number
  number: string
  row: number
  column: number
  available: boolean
}

export interface Availability {
  trip_id: number
  origin: NamedResource
  destination: NamedResource
  price: string
  seats: Seat[]
}
