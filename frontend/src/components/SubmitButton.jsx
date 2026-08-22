import React from 'react'

function SubmitButton({ onClick, loading, disabled, label = 'Save Invoice' }) {
  return (
    <button
      type="button"
      className="btn btn-primary"
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? 'Saving…' : label}
    </button>
  )
}

export default SubmitButton
