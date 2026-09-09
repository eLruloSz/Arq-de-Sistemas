import { apiClient } from './client'
import { getAllPages } from './pagination'
import type { AdminTrip, TripInput } from '../types/admin'
import type { Availability, TripSearchParams, TripSearchResult } from '../types/travel'

export const getTrips = () => getAllPages<AdminTrip>('trips/')

export async function createTrip(input: TripInput) {
  return (await apiClient.post<AdminTrip>('trips/', input)).data
}

export async function updateTrip(id: number, input: TripInput) {
  return (await apiClient.patch<AdminTrip>(`trips/${id}/`, input)).data
}

export async function searchTrips(params: TripSearchParams) {
  const response = await apiClient.get<TripSearchResult[]>('trips/search/', { params })
  return response.data
}

export async function getTripAvailability(
  tripId: number,
  origin: number,
  destination: number,
) {
  const response = await apiClient.get<Availability>(`trips/${tripId}/availability/`, {
    params: { origin, destination },
  })
  return response.data
}
