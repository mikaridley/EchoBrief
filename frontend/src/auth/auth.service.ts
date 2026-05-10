const TOKEN_KEY = 'echobrief_google_id_token'

export const authService = {
  getToken,
  setToken,
  clearToken,
  getAuthHeaders,
}

function getToken(): string {
  return sessionStorage.getItem(TOKEN_KEY) || ''
}

function setToken(token: string): void {
  if (!token) return
  sessionStorage.setItem(TOKEN_KEY, token)
}

function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}

function getAuthHeaders(): Record<string, string> {
  const token = getToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}
