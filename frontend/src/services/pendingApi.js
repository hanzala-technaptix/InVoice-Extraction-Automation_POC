import axios from 'axios'
import { parseApiError } from './invoiceApi'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { Accept: 'application/json' },
})

export { parseApiError }

export async function getPendingInvoices(status = 'pending_review') {
  const { data } = await api.get('/pending-invoices', {
    params: status ? { status } : {},
  })
  return data
}

export async function getPendingInvoiceById(pendingId) {
  const { data } = await api.get(`/pending-invoices/${pendingId}`)
  return data
}

export async function deletePendingInvoice(pendingId) {
  await api.delete(`/pending-invoices/${pendingId}`)
}

export default {
  getPendingInvoices,
  getPendingInvoiceById,
  deletePendingInvoice,
  parseApiError,
}
