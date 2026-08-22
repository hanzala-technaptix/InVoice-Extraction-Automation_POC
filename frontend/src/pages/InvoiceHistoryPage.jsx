import React, { useEffect, useState } from 'react'
import { getInvoiceById, getInvoices, parseApiError } from '../services/invoiceApi'

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}

function formatMoney(amount, currency) {
  if (amount === null || amount === undefined) return '—'
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency || 'USD',
  }).format(Number(amount))
}

function InvoiceHistoryPage({ selectedInvoiceId, onSelectInvoice, onBack, onProcessAnother }) {
  const [invoices, setInvoices] = useState([])
  const [detail, setDetail] = useState(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoadingList(true)
    setError('')

    getInvoices()
      .then((data) => {
        if (active) setInvoices(Array.isArray(data) ? data : [])
      })
      .catch((err) => {
        if (active) setError(parseApiError(err).message)
      })
      .finally(() => {
        if (active) setLoadingList(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!selectedInvoiceId) {
      setDetail(null)
      return undefined
    }

    let active = true
    setLoadingDetail(true)
    setError('')

    getInvoiceById(selectedInvoiceId)
      .then((data) => {
        if (active) setDetail(data)
      })
      .catch((err) => {
        if (active) setError(parseApiError(err).message)
      })
      .finally(() => {
        if (active) setLoadingDetail(false)
      })

    return () => {
      active = false
    }
  }, [selectedInvoiceId])

  if (selectedInvoiceId) {
    if (loadingDetail) {
      return <div className="empty">Loading invoice details…</div>
    }

    if (!detail) {
      return (
        <>
          {error ? <div className="alert alert--error">{error}</div> : null}
          <button type="button" className="btn btn-secondary" onClick={onBack}>
            Back to Saved Invoices
          </button>
        </>
      )
    }

    return (
      <>
        <div className="actions" style={{ marginTop: 0 }}>
          <button type="button" className="btn btn-secondary" onClick={onBack}>
            Back to Saved Invoices
          </button>
          <button type="button" className="btn btn-text" onClick={onProcessAnother}>
            Process Another Invoice
          </button>
        </div>

        <h2 className="page-title">Invoice Details</h2>
        <p className="page-lead">
          {detail.invoice_number} · {detail.vendor_name}
        </p>

        {error ? <div className="alert alert--error">{error}</div> : null}

        <div className="card">
          <div className="card__head">
            <h3 className="card__title">Invoice Information</h3>
          </div>
          <div className="card__body">
            <div className="detail-grid">
              <div>
                <span className="summary-item__label">Invoice Number</span>
                <div className="summary-item__value">{detail.invoice_number}</div>
              </div>
              <div>
                <span className="summary-item__label">Vendor</span>
                <div className="summary-item__value">{detail.vendor_name}</div>
              </div>
              <div>
                <span className="summary-item__label">Date</span>
                <div className="summary-item__value">{formatDate(detail.invoice_date)}</div>
              </div>
              <div>
                <span className="summary-item__label">PO Number</span>
                <div className="summary-item__value">{detail.po_number || '—'}</div>
              </div>
              <div>
                <span className="summary-item__label">Currency</span>
                <div className="summary-item__value">{detail.currency}</div>
              </div>
              <div>
                <span className="summary-item__label">Status</span>
                <div className="summary-item__value">
                  <span className="status-badge">Saved</span>
                </div>
              </div>
              <div>
                <span className="summary-item__label">Subtotal</span>
                <div className="summary-item__value">
                  {formatMoney(detail.subtotal, detail.currency)}
                </div>
              </div>
              <div>
                <span className="summary-item__label">Tax</span>
                <div className="summary-item__value">{formatMoney(detail.tax, detail.currency)}</div>
              </div>
              <div>
                <span className="summary-item__label">Total</span>
                <div className="summary-item__value">{formatMoney(detail.total, detail.currency)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card__head">
            <h3 className="card__title">Line Items</h3>
          </div>
          <div className="card__body">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Tax</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.line_items.map((item) => (
                    <tr key={item.id ?? `${item.description}-${item.total}`}>
                      <td>{item.description}</td>
                      <td>{item.quantity}</td>
                      <td>{formatMoney(item.unit_price, detail.currency)}</td>
                      <td>{formatMoney(item.tax, detail.currency)}</td>
                      <td>{formatMoney(item.total, detail.currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <h2 className="page-title">Saved Invoices</h2>
      <p className="page-lead">Approved invoices stored in the application database.</p>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <div className="card">
        <div className="card__body">
          {loadingList ? (
            <div className="empty">Loading saved invoices…</div>
          ) : invoices.length === 0 ? (
            <div className="empty">No invoices have been saved yet.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Invoice #</th>
                    <th>Vendor</th>
                    <th>Date</th>
                    <th>PO #</th>
                    <th>Currency</th>
                    <th>Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((invoice) => (
                    <tr
                      key={invoice.id}
                      className="is-clickable"
                      onClick={() => onSelectInvoice(invoice.id)}
                    >
                      <td>{invoice.invoice_number}</td>
                      <td>{invoice.vendor_name}</td>
                      <td>{formatDate(invoice.invoice_date)}</td>
                      <td>{invoice.po_number || '—'}</td>
                      <td>{invoice.currency}</td>
                      <td>{formatMoney(invoice.total, invoice.currency)}</td>
                      <td><span className="status-badge">Saved</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default InvoiceHistoryPage
