import { apiClient } from './client'
import type { Booking, BookingInput } from '../types/booking'

export async function createBooking(input: BookingInput) {
  const response = await apiClient.post<Booking>('bookings/', input)
  return response.data
}

export async function payBooking(bookingId: number) {
  const response = await apiClient.post<Booking>(`bookings/${bookingId}/pay/`)
  return response.data
}
