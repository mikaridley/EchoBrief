import { createContext, useContext, type ReactNode } from 'react'

import type { AuthMe } from '../types/api'

export type AuthContextValue = {
  me: AuthMe | null
  isLoading: boolean
  authError: string | null
  clearAuthError: () => void
  reportGoogleLoginError: () => void
  refresh: () => Promise<void>
  onLoginSuccess: (idToken: string) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

export type AuthProviderProps = {
  children: ReactNode
}
