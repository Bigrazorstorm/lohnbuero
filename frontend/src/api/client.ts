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
  addKommentar: (id: number, inhalt: string) =>
    api.post(`/tickets/${id}/kommentare`, { inhalt }),
}

// ── Dashboard ─────────────────────────────────
export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
  ampel: () => api.get('/dashboard/ampel'),
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
