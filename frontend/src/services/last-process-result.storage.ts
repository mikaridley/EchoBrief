import type { ProcessResponse } from '../types/api'

const KEY_PREFIX = 'echobrief:lastProcessResult:'

function keyForEmail(email: string) {
  return `${KEY_PREFIX}${email}`
}

function isProcessResponseShape(v: unknown): v is ProcessResponse {
  if (!v || typeof v !== 'object') return false
  const o = v as Record<string, unknown>
  return typeof o.transcript === 'string' && typeof o.summary === 'string'
}

export function loadLastProcessResult(email: string): ProcessResponse | null {
  try {
    const raw = localStorage.getItem(keyForEmail(email))
    if (!raw) return null
    const parsed: unknown = JSON.parse(raw)
    return isProcessResponseShape(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function saveLastProcessResult(email: string, result: ProcessResponse) {
  localStorage.setItem(keyForEmail(email), JSON.stringify(result))
}

export function clearLastProcessResult(email: string) {
  localStorage.removeItem(keyForEmail(email))
}
