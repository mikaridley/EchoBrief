import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { authService } from '../services/auth.service.js'
import { fetchMe } from '../services/user.service.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [me, setMe] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  async function refresh() {
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
  }

  function onLoginSuccess(idToken) {
    authService.setToken(idToken)
    refresh()
  }

  function logout() {
    authService.clearToken()
    setMe(null)
    window.location.reload()
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const value = useMemo(() => {
    return { me, isLoading, refresh, onLoginSuccess, logout }
  }, [me, isLoading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}

