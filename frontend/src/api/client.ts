import axios from 'axios'
import { useAuthStore } from '../store/auth'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ── Auth ─────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form)
  },
  me: () => api.get('/auth/me'),
}

// ── Users ─────────────────────────────────────
export const usersApi = {
  list: () => api.get('/users/'),
  create: (data: unknown) => api.post('/users/', data),
  update: (id: number, data: unknown) => api.patch(`/users/${id}`, data),
}

// ── Mandanten ─────────────────────────────────
export const mandantenApi = {
  list: (params?: Record<string, unknown>) => api.get('/mandanten/', { params }),
  get: (id: number) => api.get(`/mandanten/${id}`),
  create: (data: unknown) => api.post('/mandanten/', data),
  update: (id: number, data: unknown) => api.patch(`/mandanten/${id}`, data),
  deactivate: (id: number) => api.delete(`/mandanten/${id}`),
}

// ── Workflows ─────────────────────────────────
export const workflowsApi = {
  list: (params?: Record<string, unknown>) => api.get('/workflows/', { params }),
  get: (id: number) => api.get(`/workflows/${id}`),
  create: (data: unknown) => api.post('/workflows/', data),
  update: (id: number, data: unknown) => api.patch(`/workflows/${id}`, data),
  updateItem: (instanzId: number, itemId: number, data: unknown) =>
    api.patch(`/workflows/${instanzId}/items/${itemId}`, data),
  bulkCreateMonthly: (monat: number, jahr: number) =>
    api.post('/workflows/bulk-create-monthly', null, { params: { monat, jahr } }),
  listVorlagen: () => api.get('/workflows/vorlagen'),
  createVorlage: (data: unknown) => api.post('/workflows/vorlagen', data),
}

// ── Tickets ───────────────────────────────────
export const ticketsApi = {
  list: (params?: Record<string, unknown>) => api.get('/tickets/', { params }),
  get: (id: number) => api.get(`/tickets/${id}`),
  create: (data: unknown) => api.post('/tickets/', data),
  update: (id: number, data: unknown) => api.patch(`/tickets/${id}`, data),
  eskalieren: (id: number) => api.post(`/tickets/${id}/eskalieren`),
  addKommentar: (id: number, inhalt: string, istIntern = false, zitatId?: number) =>
    api.post(`/tickets/${id}/kommentare`, { inhalt, ist_intern: istIntern, zitat_id: zitatId }),
  kpis: () => api.get('/tickets/kpis'),
}

// ── Dashboard ─────────────────────────────────
export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
  ampel: () => api.get('/dashboard/ampel'),
  meinTag: () => api.get('/dashboard/mein-tag'),
}

// ── Dokumente ─────────────────────────────────
export const dokumenteApi = {
  list: (params?: Record<string, unknown>) => api.get('/dokumente/', { params }),
  upload: (formData: FormData) =>
    api.post('/dokumente/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  delete: (id: number) => api.delete(`/dokumente/${id}`),
}

// ── Audit Log ─────────────────────────────────
export const auditApi = {
  list: (params?: Record<string, unknown>) => api.get('/audit/', { params }),
  exportCsv: (params?: Record<string, unknown>) =>
    api.get('/audit/export/csv', { params, responseType: 'blob' }),
}

// ── Email Templates ───────────────────────────
export const emailTemplatesApi = {
  list: (params?: Record<string, unknown>) => api.get('/email-templates/', { params }),
  get: (id: number) => api.get(`/email-templates/${id}`),
  create: (data: unknown) => api.post('/email-templates/', data),
  update: (id: number, data: unknown) => api.patch(`/email-templates/${id}`, data),
  delete: (id: number) => api.delete(`/email-templates/${id}`),
  preview: (id: number, mandantId?: number) =>
    api.post(`/email-templates/${id}/preview`, null, {
      params: mandantId ? { mandant_id: mandantId } : {},
    }),
  send: (id: number, mandantId: number) =>
    api.post(`/email-templates/${id}/send`, null, { params: { mandant_id: mandantId } }),
  logs: (mandantId?: number) =>
    api.get('/email-templates/logs/', { params: mandantId ? { mandant_id: mandantId } : {} }),
}

// ── Admin Stammdaten ─────────────────────────
export const adminApi = {
  // Branchen
  listBranchen: (includeArchiviert = false) =>
    api.get('/admin/branchen', { params: { include_archiviert: includeArchiviert } }),
  createBranche: (data: unknown) => api.post('/admin/branchen', data),
  updateBranche: (id: number, data: unknown) => api.patch(`/admin/branchen/${id}`, data),
  archiveBranche: (id: number) => api.delete(`/admin/branchen/${id}`),

  // Ausgabewege
  listAusgabewege: () => api.get('/admin/ausgabewege'),
  createAusgabeweg: (data: unknown) => api.post('/admin/ausgabewege', data),
  updateAusgabeweg: (id: number, data: unknown) => api.patch(`/admin/ausgabewege/${id}`, data),
  deactivateAusgabeweg: (id: number) => api.delete(`/admin/ausgabewege/${id}`),

  // SMTP
  listSmtp: () => api.get('/admin/smtp'),
  createSmtp: (data: unknown) => api.post('/admin/smtp', data),
  updateSmtp: (id: number, data: unknown) => api.patch(`/admin/smtp/${id}`, data),
  testSmtp: (id: number, empfaenger: string) =>
    api.post(`/admin/smtp/${id}/test`, null, { params: { empfaenger } }),
  deleteSmtp: (id: number) => api.delete(`/admin/smtp/${id}`),

  // IMAP
  listImap: () => api.get('/admin/imap'),
  createImap: (data: unknown) => api.post('/admin/imap', data),
  updateImap: (id: number, data: unknown) => api.patch(`/admin/imap/${id}`, data),
  deleteImap: (id: number) => api.delete(`/admin/imap/${id}`),

  // Defaults
  listDefaults: (bereich?: string) =>
    api.get('/admin/defaults', { params: bereich ? { bereich } : {} }),
  resetDefaults: (bereich: string) => api.post(`/admin/defaults/reset/${bereich}`),

  // Upload Config
  getUploadConfig: () => api.get('/admin/upload-config'),
  updateUploadConfig: (data: unknown) => api.patch('/admin/upload-config', data),
}

// ── Ticket-Anhänge ───────────────────────────
export const ticketAnhangApi = {
  upload: (ticketId: number, formData: FormData) =>
    api.post(`/tickets/${ticketId}/anhaenge`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (ticketId: number) => api.get(`/tickets/${ticketId}/anhaenge`),
  delete: (ticketId: number, anhangId: number, begruendung: string) =>
    api.delete(`/tickets/${ticketId}/anhaenge/${anhangId}`, { params: { begruendung } }),
}
