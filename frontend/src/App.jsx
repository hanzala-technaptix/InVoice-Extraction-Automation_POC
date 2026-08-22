import React, { useEffect, useState } from 'react'
import InvoicePage from './pages/InvoicePage'
import InvoiceHistoryPage from './pages/InvoiceHistoryPage'
import { getHealth } from './services/invoiceApi'

function App() {
  const [view, setView] = useState('process')
  const [apiOnline, setApiOnline] = useState(null)
  const [selectedInvoiceId, setSelectedInvoiceId] = useState(null)

  useEffect(() => {
    let active = true

    getHealth()
      .then(() => {
        if (active) setApiOnline(true)
      })
      .catch(() => {
        if (active) setApiOnline(false)
      })

    return () => {
      active = false
    }
  }, [view])

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__inner">
          <div className="brand">
            <div className="brand__mark" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="9" y1="13" x2="15" y2="13" />
                <line x1="9" y1="17" x2="13" y2="17" />
              </svg>
            </div>
            <div>
              <h1 className="brand__name">Invoice Automation</h1>
              <p className="brand__tagline">Vendor invoice processing</p>
            </div>
          </div>

          <nav className="app-nav">
            <button
              type="button"
              className={`nav-link ${view === 'process' ? 'is-active' : ''}`}
              onClick={() => {
                setView('process')
                setSelectedInvoiceId(null)
              }}
            >
              Process Invoice
            </button>
            <button
              type="button"
              className={`nav-link ${view === 'history' ? 'is-active' : ''}`}
              onClick={() => {
                setView('history')
                setSelectedInvoiceId(null)
              }}
            >
              Saved Invoices
            </button>
          </nav>

          <div
            className={`system-status ${apiOnline === true ? 'is-online' : apiOnline === false ? 'is-offline' : ''}`}
          >
            <span className="system-status__dot" />
            {apiOnline === null ? 'Checking API…' : apiOnline ? 'System Ready' : 'API Unavailable'}
          </div>
        </div>
      </header>

      <main className="app-main">
        {view === 'process' ? (
          <InvoicePage
            onViewSaved={() => {
              setView('history')
              setSelectedInvoiceId(null)
            }}
          />
        ) : (
          <InvoiceHistoryPage
            selectedInvoiceId={selectedInvoiceId}
            onSelectInvoice={setSelectedInvoiceId}
            onBack={() => setSelectedInvoiceId(null)}
            onProcessAnother={() => {
              setView('process')
              setSelectedInvoiceId(null)
            }}
          />
        )}
      </main>
    </div>
  )
}

export default App
