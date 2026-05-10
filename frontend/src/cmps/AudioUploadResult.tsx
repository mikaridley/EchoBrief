import { ChevronDown, UserRound } from 'lucide-react'

import type { ActionItem, ProcessResponse } from '../types/api'

function getInitials(name: string): string {
  const cleaned = String(name || '').trim()
  if (!cleaned) return '?'

  const parts = cleaned.split(/\s+/).filter(Boolean)
  const first = parts[0]?.[0] || '?'
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + last).toUpperCase()
}

export type AudioUploadResultProps = {
  result: ProcessResponse | null
  error: string
  isUploading: boolean
  isDownloading: boolean
  onUploadNew: () => void
  onDownloadDocx: () => void
}

export function AudioUploadResult({
  result,
  error,
  isUploading,
  isDownloading,
  onUploadNew,
  onDownloadDocx,
}: AudioUploadResultProps) {
  if (!result) return null

  const summary = String(result.summary || '').trim()
  const transcript = String(result.transcript || '').trim()
  const participants = Array.isArray(result.participants) ? result.participants : []
  const decisions = Array.isArray(result.decisions) ? result.decisions : []
  const actionItems: ActionItem[] = Array.isArray(result.action_items) ? result.action_items : []

  return (
    <section className="audio-upload__result" aria-label="Meeting result">
      <header className="audio-upload__result-header">
        <h3 className="audio-upload__result-title">Summary</h3>
      </header>

      {summary && <p className="audio-upload__summary">{summary}</p>}

      {!!participants.length && (
        <section className="audio-upload__result-section" aria-label="Participants">
          <h4 className="audio-upload__section-title">Participants</h4>

          <div className="audio-upload__participants" role="list">
            {participants.map((name, idx) => (
              <div
                key={`${name}-${idx}`}
                className="audio-upload__participant"
                role="listitem"
                title={name}
                aria-label={name}
              >
                <span className="audio-upload__participant-icon" aria-hidden="true">
                  <UserRound />
                </span>
                <span className="audio-upload__participant-initials" aria-hidden="true">
                  {getInitials(name)}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {transcript && (
        <section className="audio-upload__result-section" aria-label="Transcript">
          <details className="audio-upload__transcript">
            <summary className="audio-upload__transcript-summary">
              <span className="audio-upload__section-title">Transcript</span>
              <span className="audio-upload__transcript-chevron" aria-hidden="true">
                <ChevronDown />
              </span>
            </summary>

            <div className="audio-upload__transcript-body">
              <p className="audio-upload__transcript-text">{transcript}</p>
            </div>
          </details>
        </section>
      )}

      {!!decisions.length && (
        <section className="audio-upload__result-section" aria-label="Decisions">
          <h4 className="audio-upload__section-title">Decisions</h4>
          <ul className="audio-upload__list">
            {decisions.map((txt, idx) => (
              <li key={`${txt}-${idx}`} className="audio-upload__list-item">
                {txt}
              </li>
            ))}
          </ul>
        </section>
      )}

      {!!actionItems.length && (
        <section className="audio-upload__result-section" aria-label="Action items">
          <h4 className="audio-upload__section-title">Action items</h4>
          <ul className="audio-upload__list">
            {actionItems.map((item, idx) => {
              const task = String(item?.task || '').trim()
              const owner = String(item?.owner || '').trim()
              if (!task) return null

              return (
                <li key={`${task}-${idx}`} className="audio-upload__list-item audio-upload__action-item">
                  <span className="audio-upload__action-task">{task}</span>
                  {owner && (
                    <span className="audio-upload__owner" title={owner} aria-label={`Owner: ${owner}`}>
                      <span className="audio-upload__owner-icon" aria-hidden="true">
                        <UserRound />
                      </span>
                      <span className="audio-upload__owner-initials" aria-hidden="true">
                        {getInitials(owner)}
                      </span>
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        </section>
      )}

      <footer className="audio-upload__actions">
        <button className="audio-upload__btn" type="button" onClick={onUploadNew} disabled={isUploading || isDownloading}>
          Upload new
        </button>

        <button className="audio-upload__btn" type="button" onClick={onDownloadDocx} disabled={isDownloading}>
          {isDownloading ? 'Preparing…' : 'Download .docx'}
        </button>

        <div className="audio-upload__status" aria-live="polite">
          {error && <p className="audio-upload__error">{error}</p>}
        </div>
      </footer>
    </section>
  )
}
