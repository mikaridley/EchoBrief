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

/** Max share of the bar (0–100) used while bytes are uploading to the server. */
const UPLOAD_PERCENT_CAP = 42
/** Bar moves toward this during server work (transcribe + summarize) until the response arrives. */
const PROCESSING_ASYMPTOTE = 93

export type ProcessProgress = {
  percent: number
  stage: 'upload' | 'processing'
}

export function uploadAudioForProcessing(
  file: File,
  onProgress?: (p: ProcessProgress) => void,
): Promise<ProcessResponse> {
  if (!file) return Promise.reject(new Error('Missing file'))

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)

    let processingTimer: ReturnType<typeof setInterval> | null = null
    let processingPercent = UPLOAD_PERCENT_CAP

    function clearProcessingTimer() {
      if (processingTimer !== null) {
        clearInterval(processingTimer)
        processingTimer = null
      }
    }

    function fail(err: Error) {
      clearProcessingTimer()
      reject(err)
    }

    xhr.upload.addEventListener('progress', (ev) => {
      if (!onProgress) return
      if (ev.lengthComputable && ev.total > 0) {
        const frac = ev.loaded / ev.total
        const percent = Math.round(frac * UPLOAD_PERCENT_CAP)
        onProgress({ percent, stage: 'upload' })
      }
    })

    xhr.upload.addEventListener('load', () => {
      if (!onProgress) return
      processingPercent = UPLOAD_PERCENT_CAP
      onProgress({ percent: processingPercent, stage: 'processing' })
      processingTimer = window.setInterval(() => {
        processingPercent += (PROCESSING_ASYMPTOTE - processingPercent) * 0.06
        if (processingPercent >= PROCESSING_ASYMPTOTE - 0.01) {
          processingPercent = PROCESSING_ASYMPTOTE
        }
        onProgress({ percent: Math.round(processingPercent), stage: 'processing' })
      }, 320)
    })

    xhr.addEventListener('load', () => {
      clearProcessingTimer()
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText) as ProcessResponse
          onProgress?.({ percent: 100, stage: 'processing' })
          resolve(data)
        } catch {
          fail(new Error('Invalid response from server'))
        }
      } else {
        let message = `Upload failed (${xhr.status})`
        try {
          const data = JSON.parse(xhr.responseText) as { detail?: unknown }
          message = detailMessage(data?.detail) || message
        } catch {
          // keep message
        }
        fail(new Error(message))
      }
    })

    xhr.addEventListener('error', () => {
      fail(new Error('Network error'))
    })

    xhr.addEventListener('abort', () => {
      fail(new Error('Upload cancelled'))
    })

    xhr.open('POST', `${appConfig.apiBaseUrl}/api/process`)
    const headers = authService.getAuthHeaders()
    for (const [key, value] of Object.entries(headers)) {
      xhr.setRequestHeader(key, value)
    }
    xhr.send(formData)
  })
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
