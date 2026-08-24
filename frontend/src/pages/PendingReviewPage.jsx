import React, { useCallback, useEffect, useState } from 'react'
import InvoiceReviewPanel from '../components/InvoiceReviewPanel'
import {
  deletePendingInvoice,
  getPendingInvoiceById,
  getPendingInvoices,
  parseApiError,
} from '../services/pendingApi'
import { mapExtractedToForm } from '../services/invoiceApi'

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}

function formatMoney(amount, currency) {
  if (amount === null || amount === undefined || amount === '') return '—'
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency || 'USD',
  }).format(Number(amount))
}

function formatStatus(status) {
  if (status === 'pending_review') return 'Pending Review'
  if (status === 'failed') return 'Failed'
  if (status === 'saved') return 'Saved'
  return status
}

function statusClass(status) {
  if (status === 'failed') return 'status-badge status-badge--warning'
  if (status === 'saved') return 'status-badge status-badge--muted'
  return 'status-badge'
}

function WorkflowStepsReview() {
  return (
    <div className="workflow">
      <div className="workflow__step is-complete">
        <span className="workflow__index">1</span>
        Detect
      </div>
      <div className="workflow__divider" />
      <div className="workflow__step is-active">
        <span className="workflow__index">2</span>
        Review
      </div>
      <div className="workflow__divider" />
      <div className="workflow__step">
        <span className="workflow__index">3</span>
        Save
      </div>
    </div>
  )
}

function PendingReviewPage({ onViewSaved }) {
  const [items, setItems] = useState([])
  const [loadingList, setLoadingList] = useState(true)
  const [loadingReview, setLoadingReview] = useState(false)
  const [error, setError] = useState('')
  const [reviewDetail, setReviewDetail] = useState(null)
  const [saved, setSaved] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  const loadPending = useCallback(async () => {
    setLoadingList(true)
    setError('')
    try {
      const data = await getPendingInvoices('pending_review')
      setItems(Array.isArray(data) ? data : [])
    } catch (requestError) {
      setItems([])
      setError(parseApiError(requestError).message)
    } finally {
      setLoadingList(false)
    }
  }, [])

  useEffect(() => {
    loadPending()
  }, [loadPending])

  const handleReview = async (pendingId) => {
    setLoadingReview(true)
    setError('')
    try {
      const detail = await getPendingInvoiceById(pendingId)
      setReviewDetail(detail)
    } catch (requestError) {
      setError(parseApiError(requestError).message)
    } finally {
      setLoadingReview(false)
    }
  }

  const handleBackToList = () => {
    setReviewDetail(null)
    setSaved(null)
    loadPending()
  }

  const handleSaved = (response) => {
    setSaved(response)
    setReviewDetail(null)
    loadPending()
  }

  const handleDelete = async (item) => {
    const label = item.invoice_number || item.filename || `invoice #${item.id}`
    if (!window.confirm(`Remove "${label}" from Pending Review?`)) {
      return
    }

    setDeletingId(item.id)
    setError('')
    try {
      await deletePendingInvoice(item.id)
      await loadPending()
    } catch (requestError) {
      setError(parseApiError(requestError).message)
    } finally {
      setDeletingId(null)
    }
  }

  if (saved) {
    return (
      <div className="page-workspace">
        <div className="workflow">
          <div className="workflow__step is-complete">
            <span className="workflow__index">1</span>
            Detect
          </div>
          <div className="workflow__divider" />
          <div className="workflow__step is-complete">
            <span className="workflow__index">2</span>
            Review
          </div>
          <div className="workflow__divider" />
          <div className="workflow__step is-active is-complete">
            <span className="workflow__index">3</span>
            Save
          </div>
        </div>

        <div className="page-workspace__body">
          <h2 className="page-title">Invoice saved successfully</h2>
          <div className="alert alert--success">The invoice has been saved to the database.</div>

          <div className="card card--flat">
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
                <span className="summary-item__label">Total</span>
                <span className="summary-item__value">
                  {formatMoney(saved.total, saved.currency)}
                </span>
              </div>
            </div>

            <div className="actions">
              <button type="button" className="btn btn-primary" onClick={handleBackToList}>
                Back to Pending Review
              </button>
              <button type="button" className="btn btn-secondary" onClick={onViewSaved}>
                View Saved Invoices
              </button>
            </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (reviewDetail) {
    const gmailSource = reviewDetail.gmail_source || {
      filename: reviewDetail.filename,
      sender: reviewDetail.sender_email,
      subject: reviewDetail.subject,
    }

    return (
      <div className="page-workspace">
        <WorkflowStepsReview />
        <div className="page-workspace__body">
          <h2 className="page-title">Review Invoice</h2>
          <p className="page-lead">
            Review and edit the automatically extracted invoice before saving.
          </p>

          <InvoiceReviewPanel
          key={reviewDetail.id}
          initialForm={mapExtractedToForm(reviewDetail.extracted_data)}
          gmailSource={gmailSource}
          pendingInvoiceId={reviewDetail.id}
          backLabel="Back to Pending Review"
          onBack={handleBackToList}
          onSaved={handleSaved}
        />
        </div>
      </div>
    )
  }

  return (
    <div className="page-workspace">
      <div className="workflow">
        <div className="workflow__step is-active">
          <span className="workflow__index">1</span>
          Pending Review
        </div>
        <div className="workflow__divider" />
        <div className="workflow__step">
          <span className="workflow__index">2</span>
          Review
        </div>
        <div className="workflow__divider" />
        <div className="workflow__step">
          <span className="workflow__index">3</span>
          Save
        </div>
      </div>

      <div className="page-workspace__body">
        <div className="page-workspace__header">
          <div>
            <h2 className="page-title">Pending Review</h2>
            <p className="page-lead">
              Invoices detected from Gmail and extracted automatically. Open one to review before
              saving.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadPending}
            disabled={loadingList}
          >
            {loadingList ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {error ? <div className="alert alert--error">{error}</div> : null}

        {loadingList ? (
          <div className="empty">Loading pending invoices…</div>
        ) : items.length === 0 ? (
          <div className="card card--flat">
            <div className="card__body">
              <div className="empty">
                No invoices are waiting for review. New Gmail PDFs will appear here after the
                background poll extracts them.
              </div>
            </div>
          </div>
        ) : (
          <div className="card card--flat">
            <div className="card__body card__body--flush">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>Invoice #</th>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Received / Source</th>
                    <th aria-label="Actions" />
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.vendor_name || '—'}</td>
                      <td>{item.invoice_number || '—'}</td>
                      <td>{formatDate(item.received_at)}</td>
                      <td>—</td>
                      <td>
                        <span className={statusClass(item.status)}>
                          {formatStatus(item.status)}
                        </span>
                      </td>
                      <td>
                        <div>{item.source === 'gmail' ? 'Gmail' : item.source}</div>
                        <div className="text-muted">{item.filename}</div>
                      </td>
                      <td>
                        <div className="actions actions--inline">
                          <button
                            type="button"
                            className="btn btn-primary btn--compact"
                            disabled={loadingReview || deletingId !== null || item.status === 'failed'}
                            onClick={() => handleReview(item.id)}
                          >
                            {loadingReview ? 'Loading…' : 'Review'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary btn--compact"
                            disabled={loadingReview || deletingId === item.id}
                            onClick={() => handleDelete(item)}
                          >
                            {deletingId === item.id ? 'Deleting…' : 'Delete'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PendingReviewPage
