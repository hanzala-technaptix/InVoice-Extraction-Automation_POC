import React from 'react'

function fieldError(errors, name) {
  return errors[name] || ''
}

function InvoiceForm({ values, errors, onChange }) {
  return (
    <>
      <div className="card">
        <div className="card__head">
          <h3 className="card__title">Invoice Details</h3>
        </div>
        <div className="card__body">
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="vendor_name">Vendor Name</label>
              <input
                id="vendor_name"
                value={values.vendor_name}
                className={fieldError(errors, 'vendor_name') ? 'is-error' : ''}
                onChange={(e) => onChange('vendor_name', e.target.value)}
              />
              {fieldError(errors, 'vendor_name') ? (
                <span className="field-msg">{fieldError(errors, 'vendor_name')}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="invoice_number">Invoice Number</label>
              <input
                id="invoice_number"
                value={values.invoice_number}
                className={fieldError(errors, 'invoice_number') ? 'is-error' : ''}
                onChange={(e) => onChange('invoice_number', e.target.value)}
              />
              {fieldError(errors, 'invoice_number') ? (
                <span className="field-msg">{fieldError(errors, 'invoice_number')}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="invoice_date">Invoice Date</label>
              <input
                id="invoice_date"
                type="date"
                value={values.invoice_date}
                className={fieldError(errors, 'invoice_date') ? 'is-error' : ''}
                onChange={(e) => onChange('invoice_date', e.target.value)}
              />
              {fieldError(errors, 'invoice_date') ? (
                <span className="field-msg">{fieldError(errors, 'invoice_date')}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="po_number">PO Number</label>
              <input
                id="po_number"
                value={values.po_number}
                onChange={(e) => onChange('po_number', e.target.value)}
              />
            </div>

            <div className="form-field">
              <label htmlFor="currency">Currency</label>
              <input
                id="currency"
                value={values.currency}
                className={fieldError(errors, 'currency') ? 'is-error' : ''}
                onChange={(e) => onChange('currency', e.target.value)}
              />
              {fieldError(errors, 'currency') ? (
                <span className="field-msg">{fieldError(errors, 'currency')}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="payment_terms">Payment Terms</label>
              <input
                id="payment_terms"
                value={values.payment_terms}
                onChange={(e) => onChange('payment_terms', e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card__head">
          <h3 className="card__title">Amounts</h3>
        </div>
        <div className="card__body">
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="subtotal">Subtotal</label>
              <input
                id="subtotal"
                type="number"
                min="0"
                step="0.01"
                value={values.subtotal}
                className={fieldError(errors, 'subtotal') ? 'is-error' : ''}
                onChange={(e) => onChange('subtotal', e.target.value)}
              />
              {fieldError(errors, 'subtotal') ? (
                <span className="field-msg">{fieldError(errors, 'subtotal')}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="tax">Tax</label>
              <input
                id="tax"
                type="number"
                min="0"
                step="0.01"
                value={values.tax}
                className={fieldError(errors, 'tax') ? 'is-error' : ''}
                onChange={(e) => onChange('tax', e.target.value)}
              />
              {fieldError(errors, 'tax') ? (
                <span className="field-msg">{fieldError(errors, 'tax')}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="total">Total</label>
              <input
                id="total"
                type="number"
                min="0"
                step="0.01"
                value={values.total}
                className={fieldError(errors, 'total') ? 'is-error' : ''}
                onChange={(e) => onChange('total', e.target.value)}
              />
              {fieldError(errors, 'total') ? (
                <span className="field-msg">{fieldError(errors, 'total')}</span>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default InvoiceForm
