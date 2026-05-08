import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { UploadCloud, X } from 'lucide-react'
import { downloadDocxFromResult, uploadAudioForProcessing } from '../services/process.service.js'
import { AudioUploadResult } from './AudioUploadResult.jsx'

const ACCEPT = ['audio/*', '.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm'].join(',')

export function AudioUpload() {
  const inputId = useId()
  const inputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const previewUrl = useMemo(() => {
    if (!file) return ''
    return URL.createObjectURL(file)
  }, [file])

  useEffect(() => {
    if (!previewUrl) return
    return () => URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  function setSingleFile(next) {
    setError('')
    setResult(null)
    setFile(next)
  }

  function onPickFile(ev) {
    const next = ev.target.files?.[0] || null
    setSingleFile(next)
  }

  function onClearFile() {
    setError('')
    setResult(null)
    setFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  function onUploadNew() {
    onClearFile()
  }

  function onOpenPicker() {
    inputRef.current?.click()
  }

  function onDragOver(ev) {
    ev.preventDefault()
    setIsDragging(true)
  }

  function onDragLeave() {
    setIsDragging(false)
  }

  function onDrop(ev) {
    ev.preventDefault()
    setIsDragging(false)

    const next = ev.dataTransfer.files?.[0] || null
    if (!next) return
    setSingleFile(next)
  }

  async function onUpload() {
    if (!file || isUploading) return
    setIsUploading(true)
    setError('')
    setResult(null)

    try {
      const data = await uploadAudioForProcessing(file)
      setResult(data)
    } catch (err) {
      setError(err?.message || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  async function onDownloadDocx() {
    if (!result || isDownloading) return
    setIsDownloading(true)
    setError('')

    try {
      const { blob, filename } = await downloadDocxFromResult(result)

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || 'meeting-summary.docx'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err?.message || 'DOCX download failed')
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <section className={`audio-upload ${result ? 'has-result' : ''}`} aria-label="Upload meeting audio">
      <header className="audio-upload__header">
        <h2 className="audio-upload__title">Upload a meeting recording</h2>
      </header>

      {!result && (
        <>
          <div
            className={`audio-upload__drop ${isDragging ? 'is-dragging' : ''}`}
            onDragOver={onDragOver}
            onDragEnter={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            role="button"
            tabIndex={0}
            onClick={onOpenPicker}
            onKeyDown={(ev) => {
              if (ev.key === 'Enter' || ev.key === ' ') onOpenPicker()
            }}
          >
            <div className="audio-upload__drop-icon" aria-hidden="true">
              <UploadCloud />
            </div>

            <div className="audio-upload__drop-content">
              <div className="audio-upload__drop-title">Drag & drop an audio file here</div>
              <div className="audio-upload__drop-hint">or click to choose a file</div>
            </div>

            <input
              id={inputId}
              ref={inputRef}
              className="audio-upload__input"
              type="file"
              accept={ACCEPT}
              multiple={false}
              onChange={onPickFile}
            />
          </div>

          {previewUrl && (
            <section className="audio-upload__player" aria-label="Audio preview">
              <audio className="audio-upload__audio" controls preload="metadata" src={previewUrl} />

              <button
                className="audio-upload__player-clear"
                type="button"
                onClick={onClearFile}
                aria-label="Remove file"
              >
                <X />
              </button>
            </section>
          )}

          <footer className="audio-upload__actions">
            <button className="audio-upload__btn" type="button" onClick={onUpload} disabled={!file || isUploading}>
              {isUploading ? 'Uploading…' : 'Upload'}
            </button>

            <div className="audio-upload__status" aria-live="polite">
              {error && <p className="audio-upload__error">{error}</p>}
            </div>
          </footer>
        </>
      )}

      <AudioUploadResult
        result={result}
        error={error}
        isUploading={isUploading}
        isDownloading={isDownloading}
        onUploadNew={onUploadNew}
        onDownloadDocx={onDownloadDocx}
      />
    </section>
  )
}

