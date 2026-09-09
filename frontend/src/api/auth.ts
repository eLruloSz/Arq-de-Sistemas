import { apiClient } from './client'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types/auth'

export async function loginRequest(credentials: LoginRequest) {
  const response = await apiClient.post<TokenResponse>('auth/token/', credentials)
  return response.data
}

export async function registerRequest(registration: RegisterRequest) {
  await apiClient.post('auth/register/', registration)
}

export async function getCurrentUser() {
  const response = await apiClient.get<User>('auth/me/')
  return response.data
}
