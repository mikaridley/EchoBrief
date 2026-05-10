import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type KeyboardEvent,
} from 'react'
import { AlertTriangle, UploadCloud, X } from 'lucide-react'
import {
  downloadDocxFromResult,
  uploadAudioForProcessing,
  type ProcessProgress,
} from '../services/process.service'
import { AudioUploadResult } from './AudioUploadResult'
import { useAuth } from '../auth/auth.context'
import type { ProcessResponse } from '../types/api'

const ACCEPT = ['audio/*', '.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm'].join(',')

export function AudioUpload() {
  const inputId = useId()
  const inputRef = useRef<HTMLInputElement>(null)

  const { me, isLoading } = useAuth()

  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<ProcessResponse | null>(null)
  const [progress, setProgress] = useState<ProcessProgress | null>(null)

  const previewUrl = useMemo(() => {
    if (!file) return ''
    return URL.createObjectURL(file)
  }, [file])

  useEffect(() => {
    if (!previewUrl) return
    return () => URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  function setSingleFile(next: File | null) {
    setError('')
    setResult(null)
    setFile(next)
  }

  function onPickFile(ev: ChangeEvent<HTMLInputElement>) {
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

  function onDragOver(ev: DragEvent<HTMLDivElement>) {
    ev.preventDefault()
    setIsDragging(true)
  }

  function onDragLeave() {
    setIsDragging(false)
  }

  function onDrop(ev: DragEvent<HTMLDivElement>) {
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
    setProgress({ percent: 0, stage: 'upload' })

    try {
      const data = await uploadAudioForProcessing(file, setProgress)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
      setProgress(null)
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
      setError(err instanceof Error ? err.message : 'DOCX download failed')
    } finally {
      setIsDownloading(false)
    }
  }

  function onDropZoneKeyDown(ev: KeyboardEvent<HTMLDivElement>) {
    if (ev.key === 'Enter' || ev.key === ' ') onOpenPicker()
  }

  return (
    <section className={`audio-upload ${result ? 'has-result' : ''}`} aria-label="Upload meeting audio">
      <header className="audio-upload__header">
        <h2 className="audio-upload__title">Upload a meeting recording</h2>
      </header>

      {!result && !isLoading && me && !me.enabled && (
        <section className="audio-upload__blocked" aria-label="Access required">
          <div className="audio-upload__blocked-row">
            <span className="audio-upload__blocked-icon" aria-hidden="true">
              <AlertTriangle />
            </span>
            <p className="audio-upload__blocked-title">Access required</p>
          </div>
          <p className="audio-upload__blocked-text">Contact admin to enable access.</p>
        </section>
      )}

      {!result && !isLoading && !me && (
        <section className="audio-upload__blocked" aria-label="Sign in required">
          <div className="audio-upload__blocked-row">
            <span className="audio-upload__blocked-icon" aria-hidden="true">
              <AlertTriangle />
            </span>
            <p className="audio-upload__blocked-title">Sign in required</p>
          </div>
          <p className="audio-upload__blocked-text">Please sign in with Google to upload and summarize.</p>
        </section>
      )}

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
            onKeyDown={onDropZoneKeyDown}
            aria-disabled={!me?.enabled}
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
              disabled={!me?.enabled}
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
            <button
              className="audio-upload__btn"
              type="button"
              onClick={onUpload}
              disabled={!me?.enabled || !file || isUploading}
            >
              {isUploading ? 'Working…' : 'Upload'}
            </button>

            <div className="audio-upload__status" aria-live="polite">
              {error && <p className="audio-upload__error">{error}</p>}
            </div>

            {isUploading && progress && (
              <div className="audio-upload__progress-wrap">
                <div className="audio-upload__progress-meta">
                  <span className="audio-upload__progress-label">
                    {progress.stage === 'upload' ? 'Sending your file…' : 'Transcribing and summarizing…'}
                  </span>
                  <span className="audio-upload__progress-pct" aria-hidden="true">
                    {progress.percent}%
                  </span>
                </div>
                <div
                  className="audio-upload__progress-track"
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={progress.percent}
                  aria-valuetext={
                    progress.stage === 'upload'
                      ? `Sending file, ${progress.percent}%`
                      : `Processing on server, ${progress.percent}%`
                  }
                >
                  <div
                    className="audio-upload__progress-fill"
                    style={{ width: `${progress.percent}%` }}
                  />
                </div>
              </div>
            )}
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
