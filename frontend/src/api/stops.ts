import { apiClient } from './client'
import type { AxiosResponse } from 'axios'
import type { PaginatedResponse, Stop } from '../types/travel'

export async function getStops() {
  const stops: Stop[] = []
  let nextUrl: string | null = 'stops/'

  while (nextUrl) {
    const response: AxiosResponse<PaginatedResponse<Stop>> = await apiClient.get(nextUrl)
    stops.push(...response.data.results)
    nextUrl = response.data.next
  }

  return stops
}
