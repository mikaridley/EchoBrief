import { useCallback, useEffect, useMemo, useState } from 'react'
import { authService } from '../services/auth.service.js'
import { fetchMe } from '../services/user.service.js'
import { AuthContext } from './auth.context.js'

export function AuthProvider({ children }) {
  const [me, setMe] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    const token = authService.getToken()
    if (!token) {
      setMe(null)
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    try {
      const data = await fetchMe()
      setMe(data)
    } catch {
      authService.clearToken()
      setMe(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const onLoginSuccess = useCallback((idToken) => {
    authService.setToken(idToken)
    refresh()
  }, [refresh])

  const logout = useCallback(() => {
    authService.clearToken()
    setMe(null)
    window.location.reload()
  }, [])

  useEffect(() => {
    let isCancelled = false

    ;(async () => {
      await Promise.resolve()
      if (isCancelled) return
      await refresh()
    })()

    return () => {
      isCancelled = true
    }
  }, [refresh])

  const value = useMemo(() => {
    return { me, isLoading, refresh, onLoginSuccess, logout }
  }, [me, isLoading, refresh, onLoginSuccess, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

