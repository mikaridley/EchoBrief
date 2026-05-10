import { appConfig } from '../config/app.config'
import { authService } from '../auth/auth.service'
import type { AuthMe } from '../types/api'

function detailMessage(detail: unknown): string | undefined {
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail && typeof (detail as { message: unknown }).message === 'string') {
    return (detail as { message: string }).message
  }
  return undefined
}

export async function fetchMe(): Promise<AuthMe> {
  const res = await fetch(`${appConfig.apiBaseUrl}/api/auth/me`, {
    headers: authService.getAuthHeaders(),
  })

  if (!res.ok) {
    let message = `Auth failed (${res.status})`
    try {
      const data = (await res.json()) as { detail?: unknown }
      message = detailMessage(data?.detail) || message
    } catch {
      // ignore
    }
    throw new Error(message)
  }

  return res.json() as Promise<AuthMe>
}
