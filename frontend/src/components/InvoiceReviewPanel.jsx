import React, { useEffect, useState } from 'react'
import InvoiceForm from './InvoiceForm'
import InvoiceItems from './InvoiceItems'
import InvoicePreview from './InvoicePreview'
import SubmitButton from './SubmitButton'
import {
  approveInvoice,
  mapBackendErrorsToFields,
  mapFormToApproveRequest,
  parseApiError,
} from '../services/invoiceApi'

const EMPTY_LINE = { description: '', quantity: '', unit_price: '', tax: 0, total: '' }

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

function GmailSourceBanner({ gmailSource }) {
  if (!gmailSource) return null

  return (
    <div className="alert alert--success">
      <strong>Received from Gmail</strong>
      {gmailSource.filename ? (
        <>
          {' '}
          · <strong>{gmailSource.filename}</strong>
        </>
      ) : null}
      {gmailSource.sender ? <> · {gmailSource.sender}</> : null}
      {gmailSource.subject ? <> · {gmailSource.subject}</> : null}
    </div>
  )
}

function InvoiceReviewPanel({
  initialForm,
  gmailSource = null,
  pendingInvoiceId = null,
  backLabel = 'Start Over',
  onBack,
  onSaved,
}) {
  const [form, setForm] = useState(initialForm)
  const [fieldErrors, setFieldErrors] = useState({})
  const [bannerError, setBannerError] = useState('')
  const [warnings, setWarnings] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setForm(initialForm)
    setFieldErrors({})
    setBannerError('')
    setWarnings([])
  }, [initialForm])

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
      const response = await approveInvoice(payload, pendingInvoiceId)
      onSaved?.(response)
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

  if (!form) return null

  return (
    <>
      <InvoicePreview phase="review" />

      <GmailSourceBanner gmailSource={gmailSource} />

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
        <button type="button" className="btn btn-text" onClick={onBack} disabled={saving}>
          {backLabel}
        </button>
      </div>
    </>
  )
}

export default InvoiceReviewPanel
