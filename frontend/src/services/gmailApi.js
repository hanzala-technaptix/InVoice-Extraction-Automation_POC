import axios from 'axios'
import { parseApiError } from './invoiceApi'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { Accept: 'application/json' },
})

export { parseApiError }

export async function getGmailStatus() {
  const { data } = await api.get('/gmail/status')
  return data
}

export async function getGmailMessages(maxResults = 20) {
  const { data } = await api.get('/gmail/messages', {
    params: { max_results: maxResults },
  })
  return data
}

export async function extractInvoiceFromGmail(messageId, attachmentId) {
  const { data } = await api.post('/gmail/extract', {
    message_id: messageId,
    attachment_id: attachmentId,
  })
  return data
}

export default {
  getGmailStatus,
  getGmailMessages,
  extractInvoiceFromGmail,
  parseApiError,
}
