export function AudioUploadResult({
  result,
  error,
  isUploading,
  isDownloading,
  onUploadNew,
  onDownloadDocx,
}) {
  if (!result) return null

  return (
    <section className="audio-upload__result" aria-label="Backend result">
      <h3 className="audio-upload__result-title">Summary</h3>

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

      <div className="audio-upload__result-block">
        <h4 className="audio-upload__result-label">Backend response</h4>
        <pre className="audio-upload__result-text">{JSON.stringify(result, null, 2)}</pre>
      </div>
    </section>
  )
}

