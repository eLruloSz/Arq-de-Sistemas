import type { AxiosResponse } from 'axios'
import { apiClient } from './client'
import type { PaginatedResponse } from '../types/travel'

export async function getAllPages<T>(initialUrl: string, params?: Record<string, unknown>) {
  const items: T[] = []
  let nextUrl: string | null = initialUrl
  let firstRequest = true

  while (nextUrl) {
    const response: AxiosResponse<PaginatedResponse<T>> = await apiClient.get(nextUrl, {
      params: firstRequest ? params : undefined,
    })
    items.push(...response.data.results)
    nextUrl = response.data.next
    firstRequest = false
  }

  return items
}
