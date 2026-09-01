import axios from 'axios'

// Cliente HTTP centralizado hacia el backend (Django REST Framework).
// La URL base se toma de una variable de entorno para no hardcodear
// localhost:8000 en el código.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})
