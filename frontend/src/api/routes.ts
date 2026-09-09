import { apiClient } from './client'
import { getAllPages } from './pagination'
import type { AdminRoute, RouteInput, RouteStop, RouteStopInput } from '../types/admin'

export const getRoutes = () => getAllPages<AdminRoute>('routes/')

export async function createRoute(input: RouteInput) {
  return (await apiClient.post<AdminRoute>('routes/', input)).data
}

export async function updateRoute(id: number, input: RouteInput) {
  return (await apiClient.patch<AdminRoute>(`routes/${id}/`, input)).data
}

export async function getRouteStops(id: number) {
  return (await apiClient.get<RouteStop[]>(`routes/${id}/stops/`)).data
}

export async function replaceRouteStops(id: number, stops: RouteStopInput[]) {
  return (await apiClient.put<RouteStop[]>(`routes/${id}/stops/`, { stops })).data
}
