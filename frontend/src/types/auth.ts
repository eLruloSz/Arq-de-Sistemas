export type UserRole = 'PASAJERO' | 'ADMINISTRADOR'

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access: string
  refresh: string
}

export interface TokenRefreshResponse {
  access: string
  refresh?: string
}

export interface RegisterRequest {
  username: string
  email: string
  first_name: string
  last_name: string
  password: string
}
