import { apiClient } from './client'
import { getAllPages } from './pagination'
import type { Bus, BusInput } from '../types/admin'

export const getBuses = () => getAllPages<Bus>('buses/')

export async function createBus(input: BusInput) {
  return (await apiClient.post<Bus>('buses/', input)).data
}

export async function updateBus(id: number, input: BusInput) {
  return (await apiClient.patch<Bus>(`buses/${id}/`, input)).data
}
