import { useCallback, useEffect, useMemo, useState } from 'react'

import type { AuthMe } from '../types/api'
import { fetchMe } from '../services/user.service'
import { authService } from './auth.service'
import { AuthContext, type AuthProviderProps } from './auth.context'

export function AuthProvider({ children }: AuthProviderProps) {
  const [me, setMe] = useState<AuthMe | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState<string | null>(null)

  const clearAuthError = useCallback(() => {
    setAuthError(null)
  }, [])

  const reportGoogleLoginError = useCallback(() => {
    setAuthError(
      'Google did not finish sign-in. Try again, or pause extensions that block Google (e.g. ad blockers) on this page.',
    )
  }, [])

  const refresh = useCallback(async () => {
    const token = authService.getToken()
    if (!token) {
      setMe(null)
      setIsLoading(false)
      setAuthError(null)
      return
    }

    setIsLoading(true)
    try {
      const data = await fetchMe()
      setMe(data)
      setAuthError(null)
    } catch (err) {
      authService.clearToken()
      setMe(null)
      const message = err instanceof Error ? err.message : 'Could not verify sign-in with the server.'
      setAuthError(message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const onLoginSuccess = useCallback(
    (idToken: string) => {
      setAuthError(null)
      authService.setToken(idToken)
      void refresh()
    },
    [refresh],
  )

  const logout = useCallback(() => {
    authService.clearToken()
    setMe(null)
    setAuthError(null)
    window.location.reload()
  }, [])

  useEffect(() => {
    let isCancelled = false

    void (async () => {
      await Promise.resolve()
      if (isCancelled) return
      await refresh()
    })()

    return () => {
      isCancelled = true
    }
  }, [refresh])

  const value = useMemo(
    () => ({
      me,
      isLoading,
      authError,
      clearAuthError,
      reportGoogleLoginError,
      refresh,
      onLoginSuccess,
      logout,
    }),
    [me, isLoading, authError, clearAuthError, reportGoogleLoginError, refresh, onLoginSuccess, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
