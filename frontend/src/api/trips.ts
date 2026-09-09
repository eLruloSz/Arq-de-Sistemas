import { apiClient } from './client'
import type { Availability, TripSearchParams, TripSearchResult } from '../types/travel'

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
