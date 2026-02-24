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
  
  // NEW (v2.1): Workflow Phasen
  listPhasen: (vorlageId: number) => api.get(`/workflows/vorlagen/${vorlageId}/phasen`),
  createPhase: (vorlageId: number, data: unknown) =>
    api.post(`/workflows/vorlagen/${vorlageId}/phasen`, data),
  updatePhase: (vorlageId: number, phaseId: number, data: unknown) =>
    api.patch(`/workflows/vorlagen/${vorlageId}/phasen/${phaseId}`, data),
  deletePhase: (vorlageId: number, phaseId: number) =>
    api.delete(`/workflows/vorlagen/${vorlageId}/phasen/${phaseId}`),
  reorderPhasen: (vorlageId: number, phaseIds: number[]) =>
    api.post(`/workflows/vorlagen/${vorlageId}/phasen/reorder`, phaseIds),
  
  // NEW (v2.1): Workflow Item Dependencies
  listDependencies: (vorlageId: number) =>
    api.get(`/workflows/vorlagen/${vorlageId}/dependencies`),
  createDependency: (vorlageId: number, data: unknown) =>
    api.post(`/workflows/vorlagen/${vorlageId}/dependencies`, data),
  updateDependency: (vorlageId: number, dependencyId: number, data: unknown) =>
    api.patch(`/workflows/vorlagen/${vorlageId}/dependencies/${dependencyId}`, data),
  deleteDependency: (vorlageId: number, dependencyId: number) =>
    api.delete(`/workflows/vorlagen/${vorlageId}/dependencies/${dependencyId}`),
  getDependencyGraph: (vorlageId: number) =>
    api.get(`/workflows/vorlagen/${vorlageId}/dependencies/graph`),
  
  // NEW (v2.1): Dependency Analysis
  getItemBlockages: (instanzId: number, itemId: number) =>
    api.get(`/workflows/${instanzId}/items/${itemId}/blockages`),
  listBlockedItems: (instanzId: number) =>
    api.get(`/workflows/${instanzId}/blocked-items`),
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

  // v2.0 Tenants
  listTenants: (includeInactive = false) =>
    api.get('/admin/tenants', { params: { include_inactive: includeInactive } }),
  createTenant: (data: unknown) => api.post('/admin/tenants', data),
  updateTenant: (id: number, data: unknown) => api.patch(`/admin/tenants/${id}`, data),
  getTenant: (id: number) => api.get(`/admin/tenants/${id}`),

  // v2.0 Abrechnungsfirmen
  listAbrechnungsfirmen: (tenantId: number, includeInactive = false) =>
    api.get(`/admin/tenants/${tenantId}/abrechnungsfirmen`, { params: { include_inactive: includeInactive } }),
  createAbrechnungsfirma: (data: unknown) => api.post('/admin/abrechnungsfirmen', data),
  updateAbrechnungsfirma: (id: number, data: unknown) => api.patch(`/admin/abrechnungsfirmen/${id}`, data),

  // v2.0 Global Events
  listGlobalEvents: (params?: Record<string, unknown>) =>
    api.get('/admin/global-events', { params }),
  getGlobalEvent: (id: number) => api.get(`/admin/global-events/${id}`),
  createGlobalEvent: (data: unknown) => api.post('/admin/global-events', data),
  updateGlobalEvent: (id: number, data: unknown) => api.patch(`/admin/global-events/${id}`, data),
  deleteGlobalEvent: (id: number) => api.delete(`/admin/global-events/${id}`),
  addGlobalEventSchritt: (eventId: number, data: unknown) =>
    api.post(`/admin/global-events/${eventId}/schritte`, data),
  updateGlobalEventSchritt: (schrittId: number, data: unknown) =>
    api.patch(`/admin/global-events/schritte/${schrittId}`, data),
  deleteGlobalEventSchritt: (schrittId: number) =>
    api.delete(`/admin/global-events/schritte/${schrittId}`),
  getGlobalEventTypen: () => api.get('/admin/global-event-typen'),

  // v2.0 Branchenspezifische Workflow-Schritte
  listBranchenWorkflowSchritte: (brancheId: number, includeInactive = false) =>
    api.get(`/admin/branchen/${brancheId}/workflow-schritte`, { params: { include_inactive: includeInactive } }),
  createBranchenWorkflowSchritt: (data: unknown) =>
    api.post('/admin/branchen-workflow-schritte', data),
  updateBranchenWorkflowSchritt: (id: number, data: unknown) =>
    api.patch(`/admin/branchen-workflow-schritte/${id}`, data),
  deleteBranchenWorkflowSchritt: (id: number) =>
    api.delete(`/admin/branchen-workflow-schritte/${id}`),
}

// ── Prozessdesigner API ───────────────────────
export const prozessDesignerApi = {
  listVorlagen: () =>
    api.get('/admin/prozess-designer/vorlagen'),
  getGraph: (vorlageId: number) =>
    api.get(`/admin/prozess-designer/${vorlageId}`),
  updateItemPosition: (itemId: number, pos_x: number, pos_y: number) =>
    api.patch(`/admin/prozess-designer/items/${itemId}/position`, { pos_x, pos_y }),
  createEdge: (vorlageId: number, sourceId: number, targetId: number, typ = 'blockiert_von', beschreibung?: string) =>
    api.post(`/admin/prozess-designer/${vorlageId}/edges`, null, {
      params: { source_item_id: sourceId, target_item_id: targetId, typ, beschreibung },
    }),
  deleteEdge: (edgeId: number) =>
    api.delete(`/admin/prozess-designer/edges/${edgeId}`),
  listChecklisten: (itemId: number, nurAktive = true) =>
    api.get(`/admin/prozess-designer/items/${itemId}/checklisten`, { params: { nur_aktive: nurAktive } }),
  createChecklistItem: (itemId: number, data: unknown) =>
    api.post(`/admin/prozess-designer/items/${itemId}/checklisten`, data),
  updateChecklistItem: (checklistId: number, data: unknown) =>
    api.patch(`/admin/prozess-designer/checklisten/${checklistId}`, data),
  deleteChecklistItem: (checklistId: number) =>
    api.delete(`/admin/prozess-designer/checklisten/${checklistId}`),
}

// ── Fristen API ───────────────────────────────
export const fristenApi = {
  listProfiles: (mandantId?: number) =>
    api.get('/fristen/profiles', { params: mandantId ? { mandant_id: mandantId } : {} }),
  getProfile: (id: number) =>
    api.get(`/fristen/profiles/${id}`),
  createProfile: (data: unknown) =>
    api.post('/fristen/profiles', data),
  updateProfile: (id: number, data: unknown) =>
    api.patch(`/fristen/profiles/${id}`, data),
  deleteProfile: (id: number) =>
    api.delete(`/fristen/profiles/${id}`),
  listVorlagen: () =>
    api.get('/fristen/vorlagen'),
}

// ── Schritt-Typen API ─────────────────────────
export const schrittTypenApi = {
  list: (includeInactive = false) =>
    api.get('/schritt-typen', { params: { include_inactive: includeInactive } }),
  get: (id: number) => api.get(`/schritt-typen/${id}`),
  create: (data: unknown) => api.post('/schritt-typen', data),
  update: (id: number, data: unknown) => api.patch(`/schritt-typen/${id}`, data),
  delete: (id: number) => api.delete(`/schritt-typen/${id}`),
  listMandantSchritte: (mandantId: number) =>
    api.get(`/schritt-typen/mandant/${mandantId}`),
  addMandantSchritt: (mandantId: number, schrittTypId: number) =>
    api.post('/schritt-typen/mandant-schritte', { mandant_id: mandantId, schritt_typ_id: schrittTypId }),
  removeMandantSchritt: (mandantId: number, schrittTypId: number) =>
    api.delete(`/schritt-typen/mandant/${mandantId}/schritt/${schrittTypId}`),
}

// ── Reporting API ─────────────────────────────
export const reportingApi = {
  mitarbeiterPunkte: (params?: Record<string, unknown>) =>
    api.get('/reporting/mitarbeiter-punkte', { params }),
  mandantenPunkte: (params?: Record<string, unknown>) =>
    api.get('/reporting/mandanten-punkte', { params }),
  exportCsv: (params?: Record<string, unknown>) =>
    api.get('/reporting/export/csv', { params, responseType: 'blob' }),
  exportExcel: (params?: Record<string, unknown>) =>
    api.get('/reporting/export/excel', { params, responseType: 'blob' }),
}

export const ticketAnhangApi = {
  upload: (ticketId: number, formData: FormData) =>
    api.post(`/tickets/${ticketId}/anhaenge`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (ticketId: number) => api.get(`/tickets/${ticketId}/anhaenge`),
  delete: (ticketId: number, anhangId: number, begruendung: string) =>
    api.delete(`/tickets/${ticketId}/anhaenge/${anhangId}`, { params: { begruendung } }),
}
