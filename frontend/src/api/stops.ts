import { apiClient } from './client'
import { getAllPages } from './pagination'
import type { Stop } from '../types/travel'

export type StopInput = Omit<Stop, 'id'>

export const getStops = () => getAllPages<Stop>('stops/')

export async function createStop(input: StopInput) {
  return (await apiClient.post<Stop>('stops/', input)).data
}

export async function updateStop(id: number, input: StopInput) {
  return (await apiClient.patch<Stop>(`stops/${id}/`, input)).data
}
