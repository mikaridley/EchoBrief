import { appConfig } from '../config/app.config.js'

export async function uploadAudioForProcessing(file) {
  if (!file) throw new Error('Missing file')

  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${appConfig.apiBaseUrl}/api/process`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    let message = `Upload failed (${res.status})`
    try {
      const data = await res.json()
      message = data?.detail || message
    } catch {
      // ignore
    }
    throw new Error(message)
  }

  return res.json()
}

