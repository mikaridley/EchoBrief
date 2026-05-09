const TOKEN_KEY = 'echobrief_google_id_token'

export const authService = {
  getToken,
  setToken,
  clearToken,
  getAuthHeaders,
}

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY) || ''
}

function setToken(token) {
  if (!token) return
  sessionStorage.setItem(TOKEN_KEY, token)
}

function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY)
}

function getAuthHeaders() {
  const token = getToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}

