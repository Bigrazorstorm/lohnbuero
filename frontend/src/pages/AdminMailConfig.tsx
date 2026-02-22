import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Edit2, Trash2, X, Send, Server, Mail, Inbox } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '../api/client'
import type { SmtpKonfiguration, ImapKonfiguration } from '../types'

type Tab = 'smtp' | 'imap'

export default function AdminMailConfig() {
  const [tab, setTab] = useState<Tab>('smtp')

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Mail-Konfiguration</h1>

      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'smtp' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setTab('smtp')}
        >
          <Send size={14} className="inline mr-1.5 -mt-0.5" />
          SMTP (Versand)
        </button>
        <button
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'imap' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setTab('imap')}
        >
          <Inbox size={14} className="inline mr-1.5 -mt-0.5" />
          IMAP (Empfang)
        </button>
      </div>

      {tab === 'smtp' ? <SmtpTab /> : <ImapTab />}
    </div>
  )
}

// ── SMTP Tab ──────────────────────────────────────────────

function SmtpTab() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [testEmail, setTestEmail] = useState('')
  const [testingId, setTestingId] = useState<number | null>(null)
  const [form, setForm] = useState({
    name: 'Standard', server: '', port: 587, tls_ssl: 'starttls',
    auth_user: '', auth_password: '', absender_email: '', reply_to: '', ist_aktiv: true,
  })

  const { data: smtps = [], isLoading } = useQuery<SmtpKonfiguration[]>({
    queryKey: ['smtp'],
    queryFn: () => adminApi.listSmtp().then(r => r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: unknown) => adminApi.createSmtp(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['smtp'] }); toast.success('SMTP-Konfiguration erstellt'); resetForm() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: unknown }) => adminApi.updateSmtp(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['smtp'] }); toast.success('Gespeichert'); setEditId(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => adminApi.deleteSmtp(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['smtp'] }); toast.success('Gelöscht') },
  })

  const testMut = useMutation({
    mutationFn: ({ id, email }: { id: number; email: string }) => adminApi.testSmtp(id, email),
    onSuccess: (res) => { toast.success(res.data.message); setTestingId(null); setTestEmail('') },
    onError: () => toast.error('Test fehlgeschlagen'),
  })

  const resetForm = () => {
    setForm({ name: 'Standard', server: '', port: 587, tls_ssl: 'starttls', auth_user: '', auth_password: '', absender_email: '', reply_to: '', ist_aktiv: true })
    setShowCreate(false)
  }

  const startEdit = (s: SmtpKonfiguration) => {
    setEditId(s.id)
    setForm({ name: s.name, server: s.server, port: s.port, tls_ssl: s.tls_ssl, auth_user: s.auth_user || '', auth_password: '', absender_email: s.absender_email, reply_to: s.reply_to || '', ist_aktiv: s.ist_aktiv })
  }

  const renderForm = (onSave: () => void, onCancel: () => void, saving: boolean) => (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="label">Name</label>
          <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>
        <div>
          <label className="label">Server *</label>
          <input className="input" placeholder="smtp.example.com" value={form.server}
            onChange={e => setForm(f => ({ ...f, server: e.target.value }))} />
        </div>
        <div>
          <label className="label">Port</label>
          <input type="number" className="input" value={form.port}
            onChange={e => setForm(f => ({ ...f, port: Number(e.target.value) }))} />
        </div>
        <div>
          <label className="label">TLS/SSL</label>
          <select className="input" value={form.tls_ssl} onChange={e => setForm(f => ({ ...f, tls_ssl: e.target.value }))}>
            <option value="starttls">STARTTLS</option>
            <option value="ssl">SSL/TLS</option>
            <option value="none">Keine</option>
          </select>
        </div>
        <div>
          <label className="label">Auth Benutzer</label>
          <input className="input" value={form.auth_user} onChange={e => setForm(f => ({ ...f, auth_user: e.target.value }))} />
        </div>
        <div>
          <label className="label">Auth Passwort</label>
          <input type="password" className="input" value={form.auth_password} placeholder={editId ? '(unverändert)' : ''}
            onChange={e => setForm(f => ({ ...f, auth_password: e.target.value }))} />
        </div>
        <div>
          <label className="label">Absender-E-Mail *</label>
          <input type="email" className="input" value={form.absender_email}
            onChange={e => setForm(f => ({ ...f, absender_email: e.target.value }))} />
        </div>
        <div>
          <label className="label">Reply-To</label>
          <input type="email" className="input" value={form.reply_to}
            onChange={e => setForm(f => ({ ...f, reply_to: e.target.value }))} />
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 cursor-pointer pb-2">
            <input type="checkbox" checked={form.ist_aktiv} onChange={e => setForm(f => ({ ...f, ist_aktiv: e.target.checked }))} />
            <span className="text-sm">Aktiv</span>
          </label>
        </div>
      </div>
      <div className="flex gap-2">
        <button className="btn-primary text-sm" onClick={onSave} disabled={!form.server || !form.absender_email || saving}>Speichern</button>
        <button className="btn-secondary text-sm" onClick={onCancel}>Abbrechen</button>
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">SMTP-Konfiguration</h2>
        <button className="btn-primary" onClick={() => { setShowCreate(true); setEditId(null) }}>
          <Plus size={16} /> Neue SMTP-Konfiguration
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-sm font-semibold mb-3">Neue SMTP-Konfiguration</h3>
          {renderForm(() => createMut.mutate(form), resetForm, createMut.isPending)}
        </div>
      )}

      {isLoading ? (
        <div className="card text-center py-8 text-gray-400">Laden...</div>
      ) : smtps.length === 0 ? (
        <div className="card text-center py-8">
          <Server size={32} className="mx-auto text-gray-300 mb-2" />
          <p className="text-gray-400">Keine SMTP-Konfiguration vorhanden</p>
        </div>
      ) : (
        <div className="space-y-3">
          {smtps.map(s => (
            <div key={s.id} className="card">
              {editId === s.id ? (
                renderForm(
                  () => {
                    const data: Record<string, unknown> = { ...form }
                    if (!data.auth_password) delete data.auth_password
                    updateMut.mutate({ id: s.id, data })
                  },
                  () => setEditId(null),
                  updateMut.isPending,
                )
              ) : (
                <div>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Mail size={16} className="text-blue-500" />
                        <span className="font-medium text-gray-900">{s.name}</span>
                        <span className="text-xs text-gray-400">{s.server}:{s.port}</span>
                        <span className={`badge ${s.ist_aktiv ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                          {s.ist_aktiv ? 'Aktiv' : 'Inaktiv'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Absender: {s.absender_email} | TLS: {s.tls_ssl.toUpperCase()}
                        {s.reply_to && ` | Reply-To: ${s.reply_to}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => setTestingId(testingId === s.id ? null : s.id)} className="btn-secondary text-xs py-1">
                        <Send size={12} /> Test
                      </button>
                      <button onClick={() => startEdit(s)} className="text-gray-400 hover:text-blue-600"><Edit2 size={15} /></button>
                      <button onClick={() => { if (confirm('SMTP-Konfiguration löschen?')) deleteMut.mutate(s.id) }}
                        className="text-gray-400 hover:text-red-500"><Trash2 size={15} /></button>
                    </div>
                  </div>
                  {testingId === s.id && (
                    <div className="mt-3 pt-3 border-t flex items-center gap-2">
                      <input type="email" className="input flex-1" placeholder="Test-Empfänger E-Mail" value={testEmail}
                        onChange={e => setTestEmail(e.target.value)} />
                      <button className="btn-primary text-sm" onClick={() => testMut.mutate({ id: s.id, email: testEmail })}
                        disabled={!testEmail || testMut.isPending}>
                        Testmail senden
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── IMAP Tab ──────────────────────────────────────────────

function ImapTab() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState({
    name: 'Standard', server: '', port: 993, tls_ssl: 'ssl',
    auth_user: '', auth_password: '', postfach: 'INBOX', ordner: '',
    polling_intervall_sekunden: 300, zuordnung_methode: 'betreff', ist_aktiv: true,
  })

  const { data: imaps = [], isLoading } = useQuery<ImapKonfiguration[]>({
    queryKey: ['imap'],
    queryFn: () => adminApi.listImap().then(r => r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: unknown) => adminApi.createImap(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['imap'] }); toast.success('IMAP-Konfiguration erstellt'); resetForm() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: unknown }) => adminApi.updateImap(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['imap'] }); toast.success('Gespeichert'); setEditId(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => adminApi.deleteImap(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['imap'] }); toast.success('Gelöscht') },
  })

  const resetForm = () => {
    setForm({ name: 'Standard', server: '', port: 993, tls_ssl: 'ssl', auth_user: '', auth_password: '', postfach: 'INBOX', ordner: '', polling_intervall_sekunden: 300, zuordnung_methode: 'betreff', ist_aktiv: true })
    setShowCreate(false)
  }

  const startEdit = (im: ImapKonfiguration) => {
    setEditId(im.id)
    setForm({
      name: im.name, server: im.server, port: im.port, tls_ssl: im.tls_ssl,
      auth_user: im.auth_user || '', auth_password: '', postfach: im.postfach,
      ordner: im.ordner || '', polling_intervall_sekunden: im.polling_intervall_sekunden,
      zuordnung_methode: im.zuordnung_methode, ist_aktiv: im.ist_aktiv,
    })
  }

  const renderForm = (onSave: () => void, onCancel: () => void, saving: boolean) => (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="label">Name</label>
          <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>
        <div>
          <label className="label">Server *</label>
          <input className="input" placeholder="imap.example.com" value={form.server}
            onChange={e => setForm(f => ({ ...f, server: e.target.value }))} />
        </div>
        <div>
          <label className="label">Port</label>
          <input type="number" className="input" value={form.port}
            onChange={e => setForm(f => ({ ...f, port: Number(e.target.value) }))} />
        </div>
        <div>
          <label className="label">TLS/SSL</label>
          <select className="input" value={form.tls_ssl} onChange={e => setForm(f => ({ ...f, tls_ssl: e.target.value }))}>
            <option value="ssl">SSL/TLS</option>
            <option value="starttls">STARTTLS</option>
            <option value="none">Keine</option>
          </select>
        </div>
        <div>
          <label className="label">Auth Benutzer</label>
          <input className="input" value={form.auth_user} onChange={e => setForm(f => ({ ...f, auth_user: e.target.value }))} />
        </div>
        <div>
          <label className="label">Auth Passwort</label>
          <input type="password" className="input" value={form.auth_password} placeholder={editId ? '(unverändert)' : ''}
            onChange={e => setForm(f => ({ ...f, auth_password: e.target.value }))} />
        </div>
        <div>
          <label className="label">Postfach</label>
          <input className="input" value={form.postfach} onChange={e => setForm(f => ({ ...f, postfach: e.target.value }))} />
        </div>
        <div>
          <label className="label">Ordner</label>
          <input className="input" placeholder="z.B. INBOX/Tickets" value={form.ordner}
            onChange={e => setForm(f => ({ ...f, ordner: e.target.value }))} />
        </div>
        <div>
          <label className="label">Polling-Intervall (Sek.)</label>
          <input type="number" min={60} className="input" value={form.polling_intervall_sekunden}
            onChange={e => setForm(f => ({ ...f, polling_intervall_sekunden: Number(e.target.value) }))} />
        </div>
        <div>
          <label className="label">Zuordnungsmethode</label>
          <select className="input" value={form.zuordnung_methode} onChange={e => setForm(f => ({ ...f, zuordnung_methode: e.target.value }))}>
            <option value="betreff">Ticket-ID im Betreff</option>
            <option value="message_id">Message-ID/Thread-ID</option>
            <option value="reply_to_token">Reply-To-Token</option>
          </select>
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 cursor-pointer pb-2">
            <input type="checkbox" checked={form.ist_aktiv} onChange={e => setForm(f => ({ ...f, ist_aktiv: e.target.checked }))} />
            <span className="text-sm">Aktiv</span>
          </label>
        </div>
      </div>
      <div className="flex gap-2">
        <button className="btn-primary text-sm" onClick={onSave} disabled={!form.server || saving}>Speichern</button>
        <button className="btn-secondary text-sm" onClick={onCancel}>Abbrechen</button>
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">IMAP-Konfiguration</h2>
        <button className="btn-primary" onClick={() => { setShowCreate(true); setEditId(null) }}>
          <Plus size={16} /> Neue IMAP-Konfiguration
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-sm font-semibold mb-3">Neue IMAP-Konfiguration</h3>
          {renderForm(() => createMut.mutate(form), resetForm, createMut.isPending)}
        </div>
      )}

      {isLoading ? (
        <div className="card text-center py-8 text-gray-400">Laden...</div>
      ) : imaps.length === 0 ? (
        <div className="card text-center py-8">
          <Inbox size={32} className="mx-auto text-gray-300 mb-2" />
          <p className="text-gray-400">Keine IMAP-Konfiguration vorhanden</p>
        </div>
      ) : (
        <div className="space-y-3">
          {imaps.map(im => (
            <div key={im.id} className="card">
              {editId === im.id ? (
                renderForm(
                  () => {
                    const data: Record<string, unknown> = { ...form }
                    if (!data.auth_password) delete data.auth_password
                    updateMut.mutate({ id: im.id, data })
                  },
                  () => setEditId(null),
                  updateMut.isPending,
                )
              ) : (
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Inbox size={16} className="text-green-500" />
                      <span className="font-medium text-gray-900">{im.name}</span>
                      <span className="text-xs text-gray-400">{im.server}:{im.port}</span>
                      <span className={`badge ${im.ist_aktiv ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                        {im.ist_aktiv ? 'Aktiv' : 'Inaktiv'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Postfach: {im.postfach}{im.ordner && ` / ${im.ordner}`} | Polling: {im.polling_intervall_sekunden}s |
                      Zuordnung: {im.zuordnung_methode}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => startEdit(im)} className="text-gray-400 hover:text-blue-600"><Edit2 size={15} /></button>
                    <button onClick={() => { if (confirm('IMAP-Konfiguration löschen?')) deleteMut.mutate(im.id) }}
                      className="text-gray-400 hover:text-red-500"><Trash2 size={15} /></button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
