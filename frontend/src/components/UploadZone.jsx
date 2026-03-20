import { useState, useRef } from 'react'

export default function UploadZone({ onUpload }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const certInputRef = useRef(null)
  const [certFile, setCertFile] = useState(null)

  function maybeUpload(nextCert) {
    if (nextCert) onUpload(nextCert)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      setCertFile(file)
      maybeUpload(file)
    }
  }

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave() {
    setIsDragOver(false)
  }

  function handleClick() {
    certInputRef.current?.click()
  }

  function handleCertChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setCertFile(file)
    maybeUpload(file)
  }

  function handleRunClick(e) {
    e.stopPropagation()
    if (!certFile) return
    maybeUpload(certFile)
  }

  return (
    <div
      className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={certInputRef}
        type="file"
        accept="application/pdf,image/png,image/jpeg,image/tiff"
        onChange={handleCertChange}
        hidden
      />

      <div className="upload-card">
        <div className="upload-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="12" y1="18" x2="12" y2="12" />
            <polyline points="9 15 12 12 15 15" />
          </svg>
        </div>

        <p className="upload-text">
          Upload certificate to run extraction
        </p>
        <p className="upload-hint">
          Reference Material Certificate for VLM vs OCR+LLM comparison
        </p>
        <p className="upload-hint" style={{ marginTop: 4 }}>
          Auto-runs after certificate upload. Upload master XML after extraction to compare.
        </p>

        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginTop: 8 }}>
          <button
            type="button"
            className="btn-download"
            onClick={(e) => {
              e.stopPropagation()
              certInputRef.current?.click()
            }}
          >
            Upload Certificate
          </button>
          <button
            type="button"
            className="btn-download"
            onClick={handleRunClick}
            disabled={!certFile}
            style={{ opacity: certFile ? 1 : 0.6, cursor: certFile ? 'pointer' : 'not-allowed' }}
          >
            Run Benchmark
          </button>
        </div>

        {certFile && (
          <div style={{ marginTop: 10, color: 'var(--text-muted)', fontSize: 12 }}>
            {`Certificate: ${certFile.name}`}
          </div>
        )}

        <div className="upload-formats">
          <span className="format-badge">PDF</span>
          <span className="format-badge">PNG</span>
          <span className="format-badge">JPG</span>
          <span className="format-badge">TIFF</span>
        </div>
      </div>
    </div>
  )
}
