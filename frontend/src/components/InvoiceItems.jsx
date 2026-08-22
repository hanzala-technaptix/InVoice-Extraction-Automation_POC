import React from 'react'

function InvoiceItems({ items, errors, onChange, onAdd, onRemove }) {
  return (
    <div className="card">
      <div className="card__head">
        <div className="table-toolbar">
          <h3 className="card__title">Line Items</h3>
          <button type="button" className="btn btn-secondary" onClick={onAdd}>
            Add Item
          </button>
        </div>
      </div>
      <div className="card__body">
        {errors.line_items ? <div className="alert alert--error">{errors.line_items}</div> : null}

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Tax</th>
                <th>Total</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={`item-${index}`}>
                  <td>
                    <input
                      type="text"
                      className={`table-input ${errors[`line_items.${index}.description`] ? 'is-error' : ''}`}
                      value={item.description}
                      onChange={(e) => onChange(index, 'description', e.target.value)}
                    />
                    {errors[`line_items.${index}.description`] ? (
                      <div className="field-msg">{errors[`line_items.${index}.description`]}</div>
                    ) : null}
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className={`table-input table-input--num ${errors[`line_items.${index}.quantity`] ? 'is-error' : ''}`}
                      value={item.quantity}
                      onChange={(e) => onChange(index, 'quantity', e.target.value)}
                    />
                    {errors[`line_items.${index}.quantity`] ? (
                      <div className="field-msg">{errors[`line_items.${index}.quantity`]}</div>
                    ) : null}
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className={`table-input table-input--num ${errors[`line_items.${index}.unit_price`] ? 'is-error' : ''}`}
                      value={item.unit_price}
                      onChange={(e) => onChange(index, 'unit_price', e.target.value)}
                    />
                    {errors[`line_items.${index}.unit_price`] ? (
                      <div className="field-msg">{errors[`line_items.${index}.unit_price`]}</div>
                    ) : null}
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className={`table-input table-input--num ${errors[`line_items.${index}.tax`] ? 'is-error' : ''}`}
                      value={item.tax}
                      onChange={(e) => onChange(index, 'tax', e.target.value)}
                    />
                    {errors[`line_items.${index}.tax`] ? (
                      <div className="field-msg">{errors[`line_items.${index}.tax`]}</div>
                    ) : null}
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className={`table-input table-input--num ${errors[`line_items.${index}.total`] ? 'is-error' : ''}`}
                      value={item.total}
                      onChange={(e) => onChange(index, 'total', e.target.value)}
                    />
                    {errors[`line_items.${index}.total`] ? (
                      <div className="field-msg">{errors[`line_items.${index}.total`]}</div>
                    ) : null}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="link-danger"
                      onClick={() => onRemove(index)}
                      disabled={items.length === 1}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default InvoiceItems
