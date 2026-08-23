import axios from 'axios'

/**
 * Backend routes (app/api/routes/invoice.py + app/main.py):
 *   GET  /health
 *   POST /invoices/extract   multipart field: file
 *   POST /invoices/approve   JSON: ApprovedInvoiceRequest
 *   GET  /invoices           list[ApprovedInvoiceResponse]
 *   GET  /invoices/{id}      ApprovedInvoiceResponse
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { Accept: 'application/json' },
})

function detailToMessage(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'string' ? item : item.msg || JSON.stringify(item)))
      .join(' ')
  }
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
    return detail.message
  }
  return 'Request failed.'
}

export function parseApiError(error) {
  if (!error?.response) {
    return {
      message: 'Unable to reach the API. Start the backend server and try again.',
      errors: [],
      warnings: [],
      status: 0,
    }
  }

  const { status, data } = error.response
  const detail = data?.detail

  if (status === 422 && detail && typeof detail === 'object' && Array.isArray(detail.errors)) {
    return {
      message: 'Correct the highlighted fields before saving.',
      errors: detail.errors,
      warnings: detail.warnings || [],
      status,
    }
  }

  return {
    message: detailToMessage(detail),
    errors: [],
    warnings: [],
    status,
  }
}

export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}

export async function extractInvoice(file) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post('/invoices/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return data
}

export async function approveInvoice(invoice, pendingInvoiceId = null) {
  const payload = pendingInvoiceId
    ? { ...invoice, pending_invoice_id: pendingInvoiceId }
    : invoice
  const { data } = await api.post('/invoices/approve', payload)
  return data
}

export async function getInvoices() {
  const { data } = await api.get('/invoices')
  return data
}

export async function getInvoiceById(invoiceId) {
  const { data } = await api.get(`/invoices/${invoiceId}`)
  return data
}

export function mapExtractedToForm(extracted) {
  const lineItems = Array.isArray(extracted.line_items) && extracted.line_items.length > 0
    ? extracted.line_items.map((item) => ({
        description: item.description ?? '',
        quantity: item.quantity ?? '',
        unit_price: item.unit_price ?? '',
        tax: item.tax ?? 0,
        total: item.total ?? '',
      }))
    : [{ description: '', quantity: '', unit_price: '', tax: 0, total: '' }]

  return {
    vendor_name: extracted.vendor_name ?? '',
    invoice_number: extracted.invoice_number ?? '',
    invoice_date: extracted.invoice_date ? String(extracted.invoice_date).slice(0, 10) : '',
    po_number: extracted.po_number ?? '',
    currency: extracted.currency ?? 'USD',
    subtotal: extracted.subtotal ?? '',
    tax: extracted.tax ?? '',
    total: extracted.total ?? '',
    payment_terms: extracted.payment_terms ?? '',
    line_items: lineItems,
  }
}

export function mapFormToApproveRequest(form) {
  return {
    vendor_name: form.vendor_name.trim(),
    invoice_number: form.invoice_number.trim(),
    invoice_date: new Date(`${form.invoice_date}T00:00:00`).toISOString(),
    po_number: form.po_number.trim() || null,
    currency: form.currency.trim() || 'USD',
    subtotal: Number(form.subtotal),
    tax: Number(form.tax),
    total: Number(form.total),
    payment_terms: form.payment_terms.trim() || null,
    line_items: form.line_items.map((item) => ({
      description: item.description.trim(),
      quantity: Number(item.quantity),
      unit_price: Number(item.unit_price),
      tax: Number(item.tax || 0),
      total: Number(item.total),
    })),
  }
}

export function mapBackendErrorsToFields(errors) {
  const fields = {}

  errors.forEach((message) => {
    if (message.includes('Vendor name')) fields.vendor_name = message
    else if (message.includes('Invoice number')) fields.invoice_number = message
    else if (message.includes('Currency')) fields.currency = message
    else if (message.includes('Subtotal')) fields.subtotal = message
    else if (message === 'Tax cannot be negative.') fields.tax = message
    else if (message === 'Total cannot be negative.') fields.total = message
    else if (message.includes('At least one line item')) fields.line_items = message
    else if (message.startsWith('Line item')) {
      const match = message.match(/Line item (\d+)/)
      if (!match) return
      const index = Number(match[1]) - 1
      const lower = message.toLowerCase()
      if (lower.includes('description')) fields[`line_items.${index}.description`] = message
      else if (lower.includes('quantity')) fields[`line_items.${index}.quantity`] = message
      else if (lower.includes('unit price')) fields[`line_items.${index}.unit_price`] = message
      else if (lower.includes('tax')) fields[`line_items.${index}.tax`] = message
      else if (lower.includes('total')) fields[`line_items.${index}.total`] = message
    }
  })

  return fields
}

export default {
  getHealth,
  extractInvoice,
  approveInvoice,
  getInvoices,
  getInvoiceById,
  parseApiError,
  mapExtractedToForm,
  mapFormToApproveRequest,
  mapBackendErrorsToFields,
}
