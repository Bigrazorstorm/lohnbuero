import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Edit2, Archive, X, Tag, Truck, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '../api/client'
import type { Branche, AusgabewegConfig } from '../types'

type Tab = 'branchen' | 'ausgabewege'

export default function AdminStammdaten() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('branchen')

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Stammdaten-Pflege</h1>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'branchen' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setTab('branchen')}
        >
          <Tag size={14} className="inline mr-1.5 -mt-0.5" />
          Branchen
        </button>
        <button
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'ausgabewege' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setTab('ausgabewege')}
        >
          <Truck size={14} className="inline mr-1.5 -mt-0.5" />
          Ausgabewege
        </button>
      </div>

      {tab === 'branchen' ? <BranchenTab /> : <AusgabewegeTab />}
    </div>
  )
}

// ── Branchen Tab ──────────────────────────────────────────────

function BranchenTab() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [includeArchived, setIncludeArchived] = useState(false)
  const [form, setForm] = useState({ name: '', beschreibung: '', faktor: 1.0, soka_relevant: false, tags: '' })

  const { data: branchen = [], isLoading } = useQuery<Branche[]>({
    queryKey: ['branchen', includeArchived],
    queryFn: () => adminApi.listBranchen(includeArchived).then(r => r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: unknown) => adminApi.createBranche(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['branchen'] }); toast.success('Branche erstellt'); resetForm() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: unknown }) => adminApi.updateBranche(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['branchen'] }); toast.success('Gespeichert'); setEditId(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const archiveMut = useMutation({
    mutationFn: (id: number) => adminApi.archiveBranche(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['branchen'] }); toast.success('Archiviert') },
  })

  const resetForm = () => { setForm({ name: '', beschreibung: '', faktor: 1.0, soka_relevant: false, tags: '' }); setShowCreate(false) }

  const startEdit = (b: Branche) => {
    setEditId(b.id)
    setForm({ name: b.name, beschreibung: b.beschreibung || '', faktor: b.faktor, soka_relevant: b.soka_relevant, tags: b.tags || '' })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-800">Branchen</h2>
          <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer">
            <input type="checkbox" checked={includeArchived} onChange={e => setIncludeArchived(e.target.checked)} />
            Archivierte anzeigen
          </label>
        </div>
        <button className="btn-primary" onClick={() => { setShowCreate(true); setEditId(null) }}>
          <Plus size={16} /> Neue Branche
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Neue Branche</h3>
            <button onClick={resetForm} className="text-gray-400 hover:text-gray-600"><X size={16} /></button>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <div className="col-span-2">
              <label className="label">Name *</label>
              <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Faktor</label>
              <input type="number" step="0.1" min="0.1" className="input" value={form.faktor}
                onChange={e => setForm(f => ({ ...f, faktor: Number(e.target.value) }))} />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer pb-2">
                <input type="checkbox" checked={form.soka_relevant} onChange={e => setForm(f => ({ ...f, soka_relevant: e.target.checked }))} />
                <span className="text-sm">SOKA-relevant</span>
              </label>
            </div>
            <div className="col-span-2">
              <label className="label">Beschreibung</label>
              <input className="input" value={form.beschreibung} onChange={e => setForm(f => ({ ...f, beschreibung: e.target.value }))} />
            </div>
            <div className="col-span-2">
              <label className="label">Tags (JSON-Array, z.B. ["SOKA-BAU"])</label>
              <input className="input" value={form.tags} placeholder='["Tag1","Tag2"]'
                onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary text-sm" onClick={() => createMut.mutate(form)} disabled={!form.name || createMut.isPending}>
              Anlegen
            </button>
            <button className="btn-secondary text-sm" onClick={resetForm}>Abbrechen</button>
          </div>
        </div>
      )}

      {/* List */}
      {isLoading ? (
        <div className="card text-center py-8 text-gray-400">Laden...</div>
      ) : branchen.length === 0 ? (
        <div className="card text-center py-8 text-gray-400">Keine Branchen vorhanden</div>
      ) : (
        <div className="space-y-2">
          {branchen.map(b => (
            <div key={b.id} className={`card ${b.ist_archiviert ? 'opacity-50' : ''}`}>
              {editId === b.id ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-4 gap-3">
                    <div className="col-span-2">
                      <label className="label">Name</label>
                      <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                    </div>
                    <div>
                      <label className="label">Faktor</label>
                      <input type="number" step="0.1" className="input" value={form.faktor}
                        onChange={e => setForm(f => ({ ...f, faktor: Number(e.target.value) }))} />
                    </div>
                    <div className="flex items-end">
                      <label className="flex items-center gap-2 cursor-pointer pb-2">
                        <input type="checkbox" checked={form.soka_relevant} onChange={e => setForm(f => ({ ...f, soka_relevant: e.target.checked }))} />
                        <span className="text-sm">SOKA</span>
                      </label>
                    </div>
                    <div className="col-span-2">
                      <label className="label">Beschreibung</label>
                      <input className="input" value={form.beschreibung} onChange={e => setForm(f => ({ ...f, beschreibung: e.target.value }))} />
                    </div>
                    <div className="col-span-2">
                      <label className="label">Tags</label>
                      <input className="input" value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button className="btn-primary text-sm" onClick={() => updateMut.mutate({ id: b.id, data: form })} disabled={updateMut.isPending}>
                      Speichern
                    </button>
                    <button className="btn-secondary text-sm" onClick={() => setEditId(null)}>Abbrechen</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{b.name}</span>
                      <span className="text-xs text-gray-400">Faktor: {b.faktor}</span>
                      {b.soka_relevant && <span className="badge bg-orange-100 text-orange-700">SOKA</span>}
                      {b.ist_archiviert && <span className="badge bg-red-100 text-red-600">Archiviert</span>}
                    </div>
                    {b.beschreibung && <p className="text-xs text-gray-500 mt-0.5">{b.beschreibung}</p>}
                    {b.tags && (() => { try { const t = JSON.parse(b.tags); return t.length > 0 ? <div className="flex gap-1 mt-1">{t.map((tag: string) => <span key={tag} className="badge bg-blue-50 text-blue-600 text-xs">{tag}</span>)}</div> : null } catch { return null } })()}
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => startEdit(b)} className="text-gray-400 hover:text-blue-600" title="Bearbeiten"><Edit2 size={15} /></button>
                    {!b.ist_archiviert && (
                      <button onClick={() => archiveMut.mutate(b.id)} className="text-gray-400 hover:text-red-500" title="Archivieren"><Archive size={15} /></button>
                    )}
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

// ── Ausgabewege Tab ──────────────────────────────────────────

function AusgabewegeTab() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState({ name: '', beschreibung: '', beeinflusst_workflow: false, zusatz_workflow_schritt: '' })

  const { data: ausgabewege = [], isLoading } = useQuery<AusgabewegConfig[]>({
    queryKey: ['ausgabewege'],
    queryFn: () => adminApi.listAusgabewege().then(r => r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: unknown) => adminApi.createAusgabeweg(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['ausgabewege'] }); toast.success('Ausgabeweg erstellt'); resetForm() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: unknown }) => adminApi.updateAusgabeweg(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['ausgabewege'] }); toast.success('Gespeichert'); setEditId(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Fehler'),
  })

  const deactivateMut = useMutation({
    mutationFn: (id: number) => adminApi.deactivateAusgabeweg(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['ausgabewege'] }); toast.success('Deaktiviert') },
  })

  const resetForm = () => { setForm({ name: '', beschreibung: '', beeinflusst_workflow: false, zusatz_workflow_schritt: '' }); setShowCreate(false) }

  const startEdit = (a: AusgabewegConfig) => {
    setEditId(a.id)
    setForm({ name: a.name, beschreibung: a.beschreibung || '', beeinflusst_workflow: a.beeinflusst_workflow, zusatz_workflow_schritt: a.zusatz_workflow_schritt || '' })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">Ausgabewege</h2>
        <button className="btn-primary" onClick={() => { setShowCreate(true); setEditId(null) }}>
          <Plus size={16} /> Neuer Ausgabeweg
        </button>
      </div>

      {showCreate && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Neuer Ausgabeweg</h3>
            <button onClick={resetForm} className="text-gray-400 hover:text-gray-600"><X size={16} /></button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Name *</label>
              <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Beschreibung</label>
              <input className="input" value={form.beschreibung} onChange={e => setForm(f => ({ ...f, beschreibung: e.target.value }))} />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer pb-2">
                <input type="checkbox" checked={form.beeinflusst_workflow} onChange={e => setForm(f => ({ ...f, beeinflusst_workflow: e.target.checked }))} />
                <span className="text-sm">Beeinflusst Workflow</span>
              </label>
            </div>
            {form.beeinflusst_workflow && (
              <div>
                <label className="label">Zusatz-Workflow-Schritt</label>
                <input className="input" value={form.zusatz_workflow_schritt} placeholder="z.B. Upload ins Portal"
                  onChange={e => setForm(f => ({ ...f, zusatz_workflow_schritt: e.target.value }))} />
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <button className="btn-primary text-sm" onClick={() => createMut.mutate(form)} disabled={!form.name || createMut.isPending}>Anlegen</button>
            <button className="btn-secondary text-sm" onClick={resetForm}>Abbrechen</button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="card text-center py-8 text-gray-400">Laden...</div>
      ) : ausgabewege.length === 0 ? (
        <div className="card text-center py-8 text-gray-400">Keine Ausgabewege vorhanden</div>
      ) : (
        <div className="space-y-2">
          {ausgabewege.map(a => (
            <div key={a.id} className={`card ${!a.ist_aktiv ? 'opacity-50' : ''}`}>
              {editId === a.id ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="label">Name</label>
                      <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                    </div>
                    <div>
                      <label className="label">Beschreibung</label>
                      <input className="input" value={form.beschreibung} onChange={e => setForm(f => ({ ...f, beschreibung: e.target.value }))} />
                    </div>
                    <div className="flex items-end">
                      <label className="flex items-center gap-2 cursor-pointer pb-2">
                        <input type="checkbox" checked={form.beeinflusst_workflow} onChange={e => setForm(f => ({ ...f, beeinflusst_workflow: e.target.checked }))} />
                        <span className="text-sm">Beeinflusst Workflow</span>
                      </label>
                    </div>
                    {form.beeinflusst_workflow && (
                      <div>
                        <label className="label">Zusatz-Schritt</label>
                        <input className="input" value={form.zusatz_workflow_schritt}
                          onChange={e => setForm(f => ({ ...f, zusatz_workflow_schritt: e.target.value }))} />
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button className="btn-primary text-sm" onClick={() => updateMut.mutate({ id: a.id, data: form })} disabled={updateMut.isPending}>Speichern</button>
                    <button className="btn-secondary text-sm" onClick={() => setEditId(null)}>Abbrechen</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{a.name}</span>
                      {!a.ist_aktiv && <span className="badge bg-red-100 text-red-600">Inaktiv</span>}
                      {a.beeinflusst_workflow && <span className="badge bg-purple-100 text-purple-600">Workflow</span>}
                    </div>
                    {a.beschreibung && <p className="text-xs text-gray-500 mt-0.5">{a.beschreibung}</p>}
                    {a.zusatz_workflow_schritt && <p className="text-xs text-purple-500 mt-0.5">Zusatz-Schritt: {a.zusatz_workflow_schritt}</p>}
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => startEdit(a)} className="text-gray-400 hover:text-blue-600" title="Bearbeiten"><Edit2 size={15} /></button>
                    {a.ist_aktiv && (
                      <button onClick={() => deactivateMut.mutate(a.id)} className="text-gray-400 hover:text-red-500" title="Deaktivieren"><Archive size={15} /></button>
                    )}
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
