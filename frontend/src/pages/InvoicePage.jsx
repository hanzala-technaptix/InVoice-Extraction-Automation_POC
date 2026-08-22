import React, { useState } from 'react'
import InvoiceUpload from '../components/InvoiceUpload'
import InvoicePreview from '../components/InvoicePreview'
import InvoiceForm from '../components/InvoiceForm'
import InvoiceItems from '../components/InvoiceItems'
import SubmitButton from '../components/SubmitButton'
import {
  approveInvoice,
  extractInvoice,
  mapBackendErrorsToFields,
  mapExtractedToForm,
  mapFormToApproveRequest,
  parseApiError,
} from '../services/invoiceApi'

const PHASE = {
  UPLOAD: 'upload',
  PROCESSING: 'processing',
  REVIEW: 'review',
  SAVED: 'saved',
}

const EMPTY_LINE = { description: '', quantity: '', unit_price: '', tax: 0, total: '' }

function WorkflowSteps({ phase }) {
  const uploadDone = phase !== PHASE.UPLOAD
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

function validateBeforeSubmit(form) {
  const errors = {}

  if (!form.vendor_name.trim()) errors.vendor_name = 'Vendor name is required.'
  if (!form.invoice_number.trim()) errors.invoice_number = 'Invoice number is required.'
  if (!form.invoice_date) errors.invoice_date = 'Invoice date is required.'
  if (!form.currency.trim()) errors.currency = 'Currency is required.'

  ;['subtotal', 'tax', 'total'].forEach((key) => {
    const value = Number(form[key])
    if (form[key] === '' || Number.isNaN(value)) {
      errors[key] = `${key.charAt(0).toUpperCase()}${key.slice(1)} is required.`
    } else if (value < 0) {
      errors[key] = `${key.charAt(0).toUpperCase()}${key.slice(1)} cannot be negative.`
    }
  })

  if (!form.line_items.length) {
    errors.line_items = 'At least one line item is required.'
  }

  form.line_items.forEach((item, index) => {
    if (!item.description.trim()) {
      errors[`line_items.${index}.description`] = 'Description is required.'
    }
    const qty = Number(item.quantity)
    if (item.quantity === '' || Number.isNaN(qty)) {
      errors[`line_items.${index}.quantity`] = 'Quantity is required.'
    } else if (qty <= 0) {
      errors[`line_items.${index}.quantity`] = 'Quantity must be greater than zero.'
    }
    const unitPrice = Number(item.unit_price)
    if (item.unit_price === '' || Number.isNaN(unitPrice)) {
      errors[`line_items.${index}.unit_price`] = 'Unit price is required.'
    } else if (unitPrice < 0) {
      errors[`line_items.${index}.unit_price`] = 'Unit price cannot be negative.'
    }
    const tax = Number(item.tax || 0)
    if (Number.isNaN(tax) || tax < 0) {
      errors[`line_items.${index}.tax`] = 'Tax cannot be negative.'
    }
    const total = Number(item.total)
    if (item.total === '' || Number.isNaN(total)) {
      errors[`line_items.${index}.total`] = 'Total is required.'
    } else if (total < 0) {
      errors[`line_items.${index}.total`] = 'Total cannot be negative.'
    }
  })

  return errors
}

function InvoicePage({ onViewSaved }) {
  const [phase, setPhase] = useState(PHASE.UPLOAD)
  const [file, setFile] = useState(null)
  const [form, setForm] = useState(null)
  const [saved, setSaved] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [bannerError, setBannerError] = useState('')
  const [warnings, setWarnings] = useState([])
  const [extracting, setExtracting] = useState(false)
  const [saving, setSaving] = useState(false)

  const reset = () => {
    setPhase(PHASE.UPLOAD)
    setFile(null)
    setForm(null)
    setSaved(null)
    setFieldErrors({})
    setBannerError('')
    setWarnings([])
    setExtracting(false)
    setSaving(false)
  }

  const handleFileSelect = (nextFile) => {
    setBannerError('')
    setFieldErrors({})

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
    setWarnings([])

    try {
      const extracted = await extractInvoice(file)
      setForm(mapExtractedToForm(extracted))
      setPhase(PHASE.REVIEW)
    } catch (error) {
      setPhase(PHASE.UPLOAD)
      setBannerError(parseApiError(error).message)
    } finally {
      setExtracting(false)
    }
  }

  const updateField = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }))
    setFieldErrors((current) => {
      const next = { ...current }
      delete next[name]
      return next
    })
  }

  const updateLineItem = (index, name, value) => {
    setForm((current) => ({
      ...current,
      line_items: current.line_items.map((item, i) =>
        i === index ? { ...item, [name]: value } : item,
      ),
    }))
    setFieldErrors((current) => {
      const next = { ...current }
      delete next[`line_items.${index}.${name}`]
      delete next.line_items
      return next
    })
  }

  const addLineItem = () => {
    setForm((current) => ({
      ...current,
      line_items: [...current.line_items, { ...EMPTY_LINE }],
    }))
  }

  const removeLineItem = (index) => {
    setForm((current) => ({
      ...current,
      line_items: current.line_items.filter((_, i) => i !== index),
    }))
  }

  const handleSave = async () => {
    const clientErrors = validateBeforeSubmit(form)
    if (Object.keys(clientErrors).length > 0) {
      setFieldErrors(clientErrors)
      setBannerError('Correct the highlighted fields before saving.')
      return
    }

    setSaving(true)
    setBannerError('')
    setWarnings([])

    try {
      const payload = mapFormToApproveRequest(form)
      const response = await approveInvoice(payload)
      setSaved(response)
      setPhase(PHASE.SAVED)
    } catch (error) {
      const parsed = parseApiError(error)
      setBannerError(parsed.message)
      if (parsed.errors.length) {
        setFieldErrors(mapBackendErrorsToFields(parsed.errors))
      }
      if (parsed.warnings.length) {
        setWarnings(parsed.warnings)
      }
    } finally {
      setSaving(false)
    }
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
        <InvoicePreview phase="review" />

        {bannerError ? <div className="alert alert--error">{bannerError}</div> : null}
        {warnings.length ? (
          <div className="alert alert--warning">
            {warnings.map((warning) => (
              <div key={warning}>{warning}</div>
            ))}
          </div>
        ) : null}

        <InvoiceForm values={form} errors={fieldErrors} onChange={updateField} />
        <InvoiceItems
          items={form.line_items}
          errors={fieldErrors}
          onChange={updateLineItem}
          onAdd={addLineItem}
          onRemove={removeLineItem}
        />

        <div className="actions">
          <SubmitButton onClick={handleSave} loading={saving} disabled={saving} />
          <button type="button" className="btn btn-text" onClick={reset} disabled={saving}>
            Start Over
          </button>
        </div>
      </>
    )
  }

  return (
    <>
      <WorkflowSteps phase={phase} />
      <h2 className="page-title">Upload Invoice</h2>
      <p className="page-lead">Upload a vendor PDF to extract invoice data for review and approval.</p>

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
  )
}

export default InvoicePage
