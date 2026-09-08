import axios from 'axios'

function firstMessage(value: unknown): string | null {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.find((item): item is string => typeof item === 'string') ?? null
  }
  return null
}

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError(error)) return fallback
  if (error.response?.status === 401) return 'Usuario o contraseña incorrectos.'

  const data: unknown = error.response?.data
  if (!data || typeof data !== 'object') return fallback

  const fields = data as Record<string, unknown>
  const usernameMessage = firstMessage(fields.username)
  if (usernameMessage) {
    return usernameMessage.toLowerCase().includes('already')
      ? 'Este nombre de usuario ya está en uso.'
      : usernameMessage
  }

  return (
    firstMessage(fields.email) ??
    firstMessage(fields.password) ??
    firstMessage(fields.detail) ??
    firstMessage(fields.non_field_errors) ??
    fallback
  )
}
