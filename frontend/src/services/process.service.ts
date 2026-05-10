import { appConfig } from '../config/app.config'
import { authService } from '../auth/auth.service'
import type { ProcessResponse } from '../types/api'

function detailMessage(detail: unknown): string | undefined {
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail && typeof (detail as { message: unknown }).message === 'string') {
    return (detail as { message: string }).message
  }
  return undefined
}

export async function uploadAudioForProcessing(file: File): Promise<ProcessResponse> {
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
      const data = (await res.json()) as { detail?: unknown }
      message = detailMessage(data?.detail) || message
    } catch {
      // ignore
    }
    throw new Error(message)
  }

  return res.json() as Promise<ProcessResponse>
}

export async function downloadDocxFromResult(result: ProcessResponse): Promise<{ blob: Blob; filename: string }> {
  if (!result) throw new Error('Missing result')

  const res = await fetch(`${appConfig.apiBaseUrl}/api/docx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authService.getAuthHeaders() },
    body: JSON.stringify(result),
  })

  if (!res.ok) {
    let message = `DOCX download failed (${res.status})`
    try {
      const data = (await res.json()) as { detail?: unknown }
      message = detailMessage(data?.detail) || message
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
