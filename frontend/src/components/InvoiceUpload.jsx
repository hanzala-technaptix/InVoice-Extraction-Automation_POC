import React, { useRef, useState } from 'react'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function InvoiceUpload({ file, onSelect, disabled, error }) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const pickFile = (fileList) => {
    const next = fileList?.[0]
    if (next) onSelect(next)
  }

  return (
    <div className="card">
      <div className="card__head">
        <h2 className="card__title">Upload Invoice PDF</h2>
      </div>
      <div className="card__body">
        {error ? <div className="alert alert--error">{error}</div> : null}

        <div
          className={`upload ${dragOver ? 'is-dragover' : ''}`}
          onDragOver={(event) => {
            event.preventDefault()
            if (!disabled) setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragOver(false)
            if (!disabled) pickFile(event.dataTransfer.files)
          }}
        >
          <div className="upload__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <p className="upload__label">Drag and drop a PDF invoice</p>
          <p className="upload__hint">Only PDF files are accepted.</p>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            Browse Files
          </button>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            disabled={disabled}
            onChange={(event) => pickFile(event.target.files)}
          />
        </div>

        {file ? (
          <p className="upload__file">
            Selected: <strong>{file.name}</strong> ({formatBytes(file.size)})
          </p>
        ) : null}
      </div>
    </div>
  )
}

export default InvoiceUpload
