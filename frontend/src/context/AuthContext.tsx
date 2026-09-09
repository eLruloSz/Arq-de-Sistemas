import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentUser, loginRequest, registerRequest } from '../api/auth'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setAuthFailureHandler,
  storeTokens,
} from '../api/client'
import type { LoginRequest, RegisterRequest, User } from '../types/auth'
import { AuthContext } from './authContextState'

export function AuthProvider({ children }: PropsWithChildren) {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    navigate('/')
  }, [navigate])

  const login = useCallback(async (credentials: LoginRequest) => {
    const tokens = await loginRequest(credentials)
    storeTokens(tokens)
    try {
      setUser(await getCurrentUser())
    } catch (error) {
      clearTokens()
      throw error
    }
  }, [])

  const register = useCallback(async (registration: RegisterRequest) => {
    await registerRequest(registration)
  }, [])

  useEffect(() => {
    setAuthFailureHandler(() => {
      setUser(null)
      navigate('/login', { replace: true })
    })
    return () => setAuthFailureHandler(null)
  }, [navigate])

  useEffect(() => {
    let active = true

    async function restoreSession() {
      if (!getAccessToken() && !getRefreshToken()) {
        if (active) setIsLoading(false)
        return
      }

      try {
        const currentUser = await getCurrentUser()
        if (active) setUser(currentUser)
      } catch {
        clearTokens()
        if (active) setUser(null)
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void restoreSession()
    return () => {
      active = false
    }
  }, [])

  const isAdmin = user?.role === 'ADMINISTRADOR'
  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isAdmin,
      isLoading,
      login,
      register,
      logout,
    }),
    [isAdmin, isLoading, login, logout, register, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
