import React from 'react'

function InvoicePreview({ phase }) {
  if (phase === 'processing') {
    return (
      <div className="card">
        <div className="processing">
          <div className="processing__spinner" aria-hidden="true" />
          <p className="processing__title">Analyzing invoice…</p>
          <p className="processing__detail">Extracting invoice details from the uploaded PDF.</p>
        </div>
      </div>
    )
  }

  if (phase === 'review') {
    return (
      <div>
        <h2 className="page-title">Review Invoice</h2>
        <p className="page-lead">Review the extracted information before saving.</p>
      </div>
    )
  }

  return null
}

export default InvoicePreview
