import axios, { type InternalAxiosRequestConfig } from 'axios'
import type { TokenResponse, TokenRefreshResponse } from '../types/auth'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

const refreshClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function storeTokens(tokens: TokenResponse) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

let refreshPromise: Promise<string> | null = null
let authFailureHandler: (() => void) | null = null

export function setAuthFailureHandler(handler: (() => void) | null) {
  authFailureHandler = handler
}

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('No refresh token available')

  const response = await refreshClient.post<TokenRefreshResponse>(
    'auth/token/refresh/',
    { refresh },
  )
  localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access)
  if (response.data.refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh)
  }
  return response.data.access
}

apiClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

interface RetriableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error)

    const request = error.config as RetriableRequest | undefined
    const isTokenRequest = request?.url?.includes('auth/token/') ?? false
    if (error.response?.status !== 401 || !request || request._retry || isTokenRequest) {
      return Promise.reject(error)
    }

    request._retry = true
    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const accessToken = await refreshPromise
      request.headers.Authorization = `Bearer ${accessToken}`
      return apiClient(request)
    } catch (refreshError) {
      clearTokens()
      authFailureHandler?.()
      return Promise.reject(refreshError)
    }
  },
)
