import React, { useEffect, useState } from 'react'
import InvoicePage from './pages/InvoicePage'
import InvoiceHistoryPage from './pages/InvoiceHistoryPage'
import PendingReviewPage from './pages/PendingReviewPage'
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

  const switchView = (nextView) => {
    setView(nextView)
    setSelectedInvoiceId(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__bar">
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
                <p className="brand__tagline">Procurement &amp; accounts payable</p>
              </div>
            </div>

            <div
              className={`system-status ${apiOnline === true ? 'is-online' : apiOnline === false ? 'is-offline' : ''}`}
            >
              <span className="system-status__dot" />
              {apiOnline === null ? 'Checking API…' : apiOnline ? 'System Ready' : 'API Unavailable'}
            </div>
          </div>
        </div>
      </header>

      <div className="app-shell">
        <div className="app-shell__inner">
          <nav className="section-nav" aria-label="Main sections">
            <button
              type="button"
              className={`section-nav__link ${view === 'process' ? 'is-active' : ''}`}
              onClick={() => switchView('process')}
            >
              Process Invoice
            </button>
            <button
              type="button"
              className={`section-nav__link ${view === 'pending' ? 'is-active' : ''}`}
              onClick={() => switchView('pending')}
            >
              Pending Review
            </button>
            <button
              type="button"
              className={`section-nav__link ${view === 'history' ? 'is-active' : ''}`}
              onClick={() => switchView('history')}
            >
              Saved Invoices
            </button>
          </nav>

          <main className="app-main">
            {view === 'process' ? (
              <InvoicePage
                onViewSaved={() => {
                  switchView('history')
                }}
              />
            ) : view === 'pending' ? (
              <PendingReviewPage
                onViewSaved={() => {
                  switchView('history')
                }}
              />
            ) : (
              <InvoiceHistoryPage
                selectedInvoiceId={selectedInvoiceId}
                onSelectInvoice={setSelectedInvoiceId}
                onBack={() => setSelectedInvoiceId(null)}
                onProcessAnother={() => {
                  switchView('process')
                }}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

export default App
