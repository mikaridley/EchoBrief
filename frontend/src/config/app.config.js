function normalizeApiBaseUrl(value) {
  const trimmed = String(value ?? '').trim().replace(/\/+$/, '')
  return trimmed || 'http://localhost:8000'
}

export const appConfig = {
  apiBaseUrl: normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'),
}

