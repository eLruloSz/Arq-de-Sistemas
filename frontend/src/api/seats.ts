import { apiClient } from './client'
import { getAllPages } from './pagination'
import type { AdminSeat, SeatInput } from '../types/admin'

export const getSeats = () => getAllPages<AdminSeat>('seats/')

export async function createSeat(input: SeatInput) {
  return (await apiClient.post<AdminSeat>('seats/', input)).data
}

export async function updateSeat(id: number, input: SeatInput) {
  return (await apiClient.patch<AdminSeat>(`seats/${id}/`, input)).data
}
