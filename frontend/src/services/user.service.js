import { appConfig } from '../config/app.config.js'
import { authService } from '../auth/auth.service.js'

export async function fetchMe() {
  const res = await fetch(`${appConfig.apiBaseUrl}/api/auth/me`, {
    headers: authService.getAuthHeaders(),
  })

  if (!res.ok) {
    let message = `Auth failed (${res.status})`
    try {
      const data = await res.json()
      message = data?.detail?.message || data?.detail || message
    } catch {
      // ignore
    }
    const err = new Error(message)
    err.status = res.status
    throw err
  }

  return res.json()
}

