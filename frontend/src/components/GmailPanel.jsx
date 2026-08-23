import React, { useCallback, useEffect, useState } from 'react'
import {
  extractInvoiceFromGmail,
  getGmailMessages,
  getGmailStatus,
  parseApiError,
} from '../services/gmailApi'

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString()
}

function GmailPanel({ onExtractStart, onExtracted, onExtractError, disabled }) {
  const [status, setStatus] = useState({ configured: false, connected: false })
  const [messages, setMessages] = useState([])
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [extractingId, setExtractingId] = useState(null)
  const [error, setError] = useState('')

  const refreshStatus = useCallback(async () => {
    setLoadingStatus(true)
    try {
      const nextStatus = await getGmailStatus()
      setStatus(nextStatus)
      return nextStatus
    } catch (requestError) {
      setStatus({ configured: false, connected: false })
      setError(parseApiError(requestError).message)
      return { configured: false, connected: false }
    } finally {
      setLoadingStatus(false)
    }
  }, [])

  const loadMessages = useCallback(async () => {
    setLoadingMessages(true)
    setError('')
    try {
      const data = await getGmailMessages()
      setMessages(Array.isArray(data) ? data : [])
    } catch (requestError) {
      setMessages([])
      setError(parseApiError(requestError).message)
    } finally {
      setLoadingMessages(false)
    }
  }, [])

  useEffect(() => {
    refreshStatus().then((nextStatus) => {
      if (nextStatus.connected) loadMessages()
    })
  }, [refreshStatus, loadMessages])

  const handleExtract = async (messageId, attachmentId) => {
    const extractKey = `${messageId}:${attachmentId}`
    setExtractingId(extractKey)
    setError('')
    onExtractStart?.()

    try {
      const result = await extractInvoiceFromGmail(messageId, attachmentId)
      onExtracted?.(result.invoice, result.source)
    } catch (requestError) {
      const parsed = parseApiError(requestError)
      setError(parsed.message)
      onExtractError?.(parsed.message)
    } finally {
      setExtractingId(null)
    }
  }

  if (loadingStatus) {
    return <div className="empty">Checking Gmail connection…</div>
  }

  return (
    <div className="card">
      <div className="card__head">
        <div className="table-toolbar">
          <h3 className="card__title">Gmail Invoices</h3>
          {status.connected ? (
            <div className="actions actions--inline">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={loadMessages}
                disabled={disabled || loadingMessages}
              >
                {loadingMessages ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="card__body">
        {error ? <div className="alert alert--error">{error}</div> : null}

        {!status.configured ? (
          <div className="alert alert--warning">
            Add <strong>GMAIL_EMAIL</strong> and <strong>GMAIL_APP_PASSWORD</strong> to the backend
            <code>.env</code> file, then restart the API server.
          </div>
        ) : !status.connected ? (
          <div className="alert alert--error">
            Gmail IMAP login failed. Check your email and 16-digit app password in <code>.env</code>.
          </div>
        ) : loadingMessages ? (
          <div className="empty">Loading Gmail messages…</div>
        ) : messages.length === 0 ? (
          <div className="empty">No Gmail messages with PDF attachments were found.</div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>From</th>
                  <th>Received</th>
                  <th>PDF Attachment</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {messages.flatMap((message) =>
                  message.pdf_attachments.map((attachment) => {
                    const extractKey = `${message.message_id}:${attachment.attachment_id}`
                    return (
                      <tr key={extractKey}>
                        <td>{message.subject}</td>
                        <td>{message.sender}</td>
                        <td>{formatDate(message.received_at)}</td>
                        <td>{attachment.filename}</td>
                        <td>
                          <button
                            type="button"
                            className="btn btn-secondary btn--compact"
                            disabled={disabled || extractingId === extractKey}
                            onClick={() =>
                              handleExtract(message.message_id, attachment.attachment_id)
                            }
                          >
                            {extractingId === extractKey ? 'Extracting…' : 'Extract'}
                          </button>
                        </td>
                      </tr>
                    )
                  }),
                )}
              </tbody>
            </table>
          </div>
        )}

        {status.connected ? (
          <p className="page-lead" style={{ marginTop: 16, marginBottom: 0 }}>
            Select a PDF attachment to extract. Review and edit before saving — invoices are not
            auto-approved.
          </p>
        ) : null}
      </div>
    </div>
  )
}

export default GmailPanel
