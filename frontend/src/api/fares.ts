import { apiClient } from './client'
import { getAllPages } from './pagination'
import type { Fare, FareInput } from '../types/admin'

export const getFares = () => getAllPages<Fare>('fares/')

export async function createFare(input: FareInput) {
  return (await apiClient.post<Fare>('fares/', input)).data
}

export async function updateFare(id: number, input: FareInput) {
  return (await apiClient.patch<Fare>(`fares/${id}/`, input)).data
}
