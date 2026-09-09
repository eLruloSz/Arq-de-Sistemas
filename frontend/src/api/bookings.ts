import { apiClient } from './client'
import type { Booking, BookingInput } from '../types/booking'

interface BookingListResponse {
  results: Booking[]
}

export async function getBookings() {
  const response = await apiClient.get<BookingListResponse>('bookings/')
  return response.data.results
}

export async function getBooking(bookingId: number) {
  const response = await apiClient.get<Booking>(`bookings/${bookingId}/`)
  return response.data
}

export async function createBooking(input: BookingInput) {
  const response = await apiClient.post<Booking>('bookings/', input)
  return response.data
}

export async function payBooking(bookingId: number) {
  const response = await apiClient.post<Booking>(`bookings/${bookingId}/pay/`)
  return response.data
}

export async function cancelBooking(bookingId: number) {
  const response = await apiClient.post<Booking>(`bookings/${bookingId}/cancel/`)
  return response.data
}
