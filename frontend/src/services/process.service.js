import { appConfig } from '../config/app.config.js'
import { authService } from './auth.service.js'

export async function uploadAudioForProcessing(file) {
  if (!file) throw new Error('Missing file')

  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${appConfig.apiBaseUrl}/api/process`, {
    method: 'POST',
    headers: authService.getAuthHeaders(),
    body: formData,
  })

  if (!res.ok) {
    let message = `Upload failed (${res.status})`
    try {
      const data = await res.json()
      message = data?.detail?.message || data?.detail || message
    } catch {
      // ignore
    }
    throw new Error(message)
  }

  return res.json()
}

export async function downloadDocxFromResult(result) {
  if (!result) throw new Error('Missing result')

  const res = await fetch(`${appConfig.apiBaseUrl}/api/docx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authService.getAuthHeaders() },
    body: JSON.stringify(result),
  })

  if (!res.ok) {
    let message = `DOCX download failed (${res.status})`
    try {
      const data = await res.json()
      message = data?.detail?.message || data?.detail || message
    } catch {
      // ignore
    }
    throw new Error(message)
  }

  const blob = await res.blob()
  const fallbackName = 'meeting-summary.docx'
  const contentDisposition = res.headers.get('content-disposition') || ''
  const match = contentDisposition.match(/filename="([^"]+)"/i)
  const filename = match?.[1] || fallbackName

  return { blob, filename }
}

