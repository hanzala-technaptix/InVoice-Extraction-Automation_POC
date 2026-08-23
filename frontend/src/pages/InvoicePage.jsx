import React, { useState } from 'react'
import InvoiceUpload from '../components/InvoiceUpload'
import InvoicePreview from '../components/InvoicePreview'
import InvoiceReviewPanel from '../components/InvoiceReviewPanel'
import GmailPanel from '../components/GmailPanel'
import {
  extractInvoice,
  mapExtractedToForm,
  parseApiError,
} from '../services/invoiceApi'

const PHASE = {
  UPLOAD: 'upload',
  PROCESSING: 'processing',
  REVIEW: 'review',
  SAVED: 'saved',
}

const INPUT_MODE = {
  MANUAL: 'manual',
  GMAIL: 'gmail',
}

function InputSourceTabs({ mode, onChange, disabled }) {
  return (
    <div className="input-tabs">
      <button
        type="button"
        className={`input-tab ${mode === INPUT_MODE.MANUAL ? 'is-active' : ''}`}
        onClick={() => onChange(INPUT_MODE.MANUAL)}
        disabled={disabled}
      >
        Manual Upload
      </button>
      <button
        type="button"
        className={`input-tab ${mode === INPUT_MODE.GMAIL ? 'is-active' : ''}`}
        onClick={() => onChange(INPUT_MODE.GMAIL)}
        disabled={disabled}
      >
        Gmail
      </button>
    </div>
  )
}

function WorkflowSteps({ phase }) {
  const reviewDone = phase === PHASE.SAVED

  return (
    <div className="workflow">
      <div className={`workflow__step ${phase === PHASE.UPLOAD || phase === PHASE.PROCESSING ? 'is-active' : 'is-complete'}`}>
        <span className="workflow__index">1</span>
        Upload
      </div>
      <div className="workflow__divider" />
      <div className={`workflow__step ${phase === PHASE.REVIEW ? 'is-active' : reviewDone ? 'is-complete' : ''}`}>
        <span className="workflow__index">2</span>
        Review
      </div>
      <div className="workflow__divider" />
      <div className={`workflow__step ${phase === PHASE.SAVED ? 'is-active is-complete' : ''}`}>
        <span className="workflow__index">3</span>
        Save
      </div>
    </div>
  )
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString()
}

function formatMoney(amount, currency) {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency || 'USD',
  }).format(Number(amount))
}

function InvoicePage({ onViewSaved }) {
  const [phase, setPhase] = useState(PHASE.UPLOAD)
  const [inputMode, setInputMode] = useState(INPUT_MODE.MANUAL)
  const [file, setFile] = useState(null)
  const [form, setForm] = useState(null)
  const [gmailSource, setGmailSource] = useState(null)
  const [saved, setSaved] = useState(null)
  const [bannerError, setBannerError] = useState('')
  const [extracting, setExtracting] = useState(false)

  const reset = () => {
    setPhase(PHASE.UPLOAD)
    setInputMode(INPUT_MODE.MANUAL)
    setFile(null)
    setForm(null)
    setGmailSource(null)
    setSaved(null)
    setBannerError('')
    setExtracting(false)
  }

  const handleFileSelect = (nextFile) => {
    setBannerError('')

    if (!nextFile.name.toLowerCase().endsWith('.pdf')) {
      setBannerError('Only PDF files are supported.')
      return
    }
    if (nextFile.size === 0) {
      setBannerError('The selected file is empty.')
      return
    }

    setFile(nextFile)
  }

  const handleExtract = async () => {
    if (!file) {
      setBannerError('Select a PDF invoice to continue.')
      return
    }

    setPhase(PHASE.PROCESSING)
    setExtracting(true)
    setBannerError('')

    try {
      const extracted = await extractInvoice(file)
      setForm(mapExtractedToForm(extracted))
      setGmailSource(null)
      setPhase(PHASE.REVIEW)
    } catch (error) {
      setPhase(PHASE.UPLOAD)
      setBannerError(parseApiError(error).message)
    } finally {
      setExtracting(false)
    }
  }

  const handleGmailExtractStart = () => {
    setPhase(PHASE.PROCESSING)
    setExtracting(true)
    setBannerError('')
    setGmailSource(null)
  }

  const handleGmailExtracted = (invoice, source) => {
    setForm(mapExtractedToForm(invoice))
    setGmailSource(source)
    setPhase(PHASE.REVIEW)
    setExtracting(false)
  }

  const handleGmailExtractError = (message) => {
    setPhase(PHASE.UPLOAD)
    setInputMode(INPUT_MODE.GMAIL)
    setBannerError(message)
    setExtracting(false)
  }

  if (phase === PHASE.SAVED && saved) {
    return (
      <>
        <WorkflowSteps phase={phase} />
        <h2 className="page-title">Invoice saved successfully</h2>
        <div className="alert alert--success">The invoice has been saved to the database.</div>

        <div className="card">
          <div className="card__body">
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-item__label">Invoice Number</span>
                <span className="summary-item__value">{saved.invoice_number}</span>
              </div>
              <div className="summary-item">
                <span className="summary-item__label">Vendor</span>
                <span className="summary-item__value">{saved.vendor_name}</span>
              </div>
              <div className="summary-item">
                <span className="summary-item__label">Date</span>
                <span className="summary-item__value">{formatDate(saved.invoice_date)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-item__label">Total</span>
                <span className="summary-item__value">
                  {formatMoney(saved.total, saved.currency)}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-item__label">Status</span>
                <span className="summary-item__value">
                  <span className="status-badge">Saved</span>
                </span>
              </div>
            </div>

            <div className="actions">
              <button type="button" className="btn btn-primary" onClick={reset}>
                Process Another Invoice
              </button>
              <button type="button" className="btn btn-secondary" onClick={onViewSaved}>
                View Saved Invoices
              </button>
            </div>
          </div>
        </div>
      </>
    )
  }

  if (phase === PHASE.PROCESSING) {
    return (
      <>
        <WorkflowSteps phase={phase} />
        <InvoicePreview phase="processing" />
      </>
    )
  }

  if (phase === PHASE.REVIEW && form) {
    return (
      <>
        <WorkflowSteps phase={phase} />
        <InvoiceReviewPanel
          key="manual-review"
          initialForm={form}
          gmailSource={
            gmailSource
              ? {
                  filename: gmailSource.filename,
                  sender: null,
                  subject: null,
                }
              : null
          }
          onBack={reset}
          onSaved={(response) => {
            setSaved(response)
            setPhase(PHASE.SAVED)
          }}
        />
      </>
    )
  }

  return (
    <>
      <WorkflowSteps phase={phase} />
      <h2 className="page-title">Import Invoice</h2>
      <p className="page-lead">
        Upload a PDF manually or import a PDF attachment from Gmail, then review before saving.
      </p>

      <InputSourceTabs
        mode={inputMode}
        onChange={setInputMode}
        disabled={extracting}
      />

      {inputMode === INPUT_MODE.MANUAL ? (
        <>
          <InvoiceUpload
            file={file}
            onSelect={handleFileSelect}
            disabled={extracting}
            error={bannerError}
          />

          <div className="actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleExtract}
              disabled={!file || extracting}
            >
              Extract Invoice
            </button>
          </div>
        </>
      ) : (
        <GmailPanel
          disabled={extracting}
          onExtractStart={handleGmailExtractStart}
          onExtracted={handleGmailExtracted}
          onExtractError={handleGmailExtractError}
        />
      )}
    </>
  )
}

export default InvoicePage
