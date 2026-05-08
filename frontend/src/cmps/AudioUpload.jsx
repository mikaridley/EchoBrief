import { useId, useMemo, useRef, useState } from 'react'
import { UploadCloud, X, FileAudio2 } from 'lucide-react'
import { uploadAudioForProcessing } from '../services/process.service.js'

const ACCEPT = [
  'audio/*',
  '.mp3',
  '.wav',
  '.m4a',
  '.mp4',
  '.mpeg',
  '.mpga',
  '.webm',
].join(',')

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const idx = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** idx
  const digits = idx === 0 ? 0 : idx === 1 ? 0 : 1
  return `${value.toFixed(digits)} ${units[idx]}`
}

export function AudioUpload() {
  const inputId = useId()
  const inputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const fileMeta = useMemo(() => {
    if (!file) return null
    return {
      name: file.name,
      size: formatBytes(file.size),
      type: file.type || 'audio',
    }
  }, [file])

  function onPickFile(ev) {
    const next = ev.target.files?.[0] || null
    setError('')
    setResult(null)
    setFile(next)
  }

  function onClearFile() {
    setError('')
    setResult(null)
    setFile(null)
    if (inputRef.current) inputRef.current.value = ''
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
    setError('')
    setResult(null)
    setFile(next)
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

  return (
    <section className="audio-upload" aria-label="Upload meeting audio">
      <header className="audio-upload__header">
        <h2 className="audio-upload__title">Upload a meeting recording</h2>
      </header>

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
          onChange={onPickFile}
        />
      </div>

      {fileMeta && (
        <section className="audio-upload__file" aria-label="Selected file">
          <div className="audio-upload__file-icon" aria-hidden="true">
            <FileAudio2 />
          </div>

          <div className="audio-upload__file-meta">
            <div className="audio-upload__file-name">{fileMeta.name}</div>
            <div className="audio-upload__file-sub">
              <span className="audio-upload__file-size">{fileMeta.size}</span>
              <span className="audio-upload__dot" aria-hidden="true">
                ·
              </span>
              <span className="audio-upload__file-type">{fileMeta.type}</span>
            </div>
          </div>

          <button className="audio-upload__file-clear" type="button" onClick={onClearFile} aria-label="Remove file">
            <X />
          </button>
        </section>
      )}

      <footer className="audio-upload__actions">
        <button
          className="audio-upload__btn"
          type="button"
          onClick={onUpload}
          disabled={!file || isUploading}
        >
          {isUploading ? 'Uploading…' : 'Upload'}
        </button>

        <div className="audio-upload__status" aria-live="polite">
          {error && <p className="audio-upload__error">{error}</p>}
          {result && !error && <p className="audio-upload__success">Uploaded. Backend returned a response.</p>}
        </div>
      </footer>

      {result && (
        <section className="audio-upload__result" aria-label="Backend result">
          <h3 className="audio-upload__result-title">Result</h3>

          {result.summary && (
            <div className="audio-upload__result-block">
              <h4 className="audio-upload__result-label">Summary</h4>
              <p className="audio-upload__result-text">{result.summary}</p>
            </div>
          )}

          {result.transcript && (
            <div className="audio-upload__result-block">
              <h4 className="audio-upload__result-label">Transcript</h4>
              <p className="audio-upload__result-text">{result.transcript}</p>
            </div>
          )}
        </section>
      )}
    </section>
  )
}

