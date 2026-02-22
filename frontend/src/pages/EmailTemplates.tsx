import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mail, Plus, Eye, Pencil, X, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { emailTemplatesApi } from '../api/client'
import type { EmailTemplate } from '../types'

const TYP_LABELS: Record<string, string> = {
  onboarding_welcome: 'Onboarding – Begrüßung',
  onboarding_reminder: 'Onboarding – Erinnerung (Aktivierung)',
  onboarding_unterlagen: 'Onboarding – Erinnerung Unterlagen',
  unterlagen_reminder: 'Erinnerung Unterlagen',
  custom: 'Sonstige',
}

const PLACEHOLDER_INFO = [
  '{{Mandantenname}}',
  '{{Ansprechpartner}}',
  '{{Fristdatum}}',
  '{{PortalLink}}',
  '{{KanzleiName}}',
  '{{SachbearbeiterName}}',
]

export default function EmailTemplates() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<EmailTemplate | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)

  const { data: templates = [], isLoading } = useQuery<EmailTemplate[]>({
    queryKey: ['email-templates'],
    queryFn: () => emailTemplatesApi.list().then((r) => (r as { data: EmailTemplate[] }).data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => emailTemplatesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['email-templates'] })
      setSelected(null)
      toast.success('Template deaktiviert')
    },
  })

  const handlePreview = async (tmpl: EmailTemplate) => {
    try {
      const res = await emailTemplatesApi.preview(tmpl.id) as { data: { html: string } }
      setPreviewHtml(res.data.html)
    } catch {
      toast.error('Vorschau-Fehler')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Mail size={22} className="text-green-600" />
          <h1 className="text-2xl font-bold text-gray-900">E-Mail-Templates</h1>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} />
          Neues Template
        </button>
      </div>

      {/* Placeholder cheatsheet */}
      <div className="card py-3 bg-amber-50 border border-amber-200">
        <p className="text-xs font-semibold text-amber-700 mb-1.5">Verfügbare Platzhalter:</p>
        <div className="flex flex-wrap gap-2">
          {PLACEHOLDER_INFO.map((p) => (
            <code key={p} className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-mono">
              {p}
            </code>
          ))}
        </div>
      </div>

      <div className="flex gap-5">
        {/* Template list */}
        <div className={`${selected ? 'w-1/2' : 'w-full'} space-y-2`}>
          {isLoading ? (
            <div className="card text-center py-12 text-gray-400">Laden…</div>
          ) : templates.length === 0 ? (
            <div className="card text-center py-12">
              <Mail size={40} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-400">Noch keine Templates</p>
            </div>
          ) : (
            templates.map((tmpl) => (
              <div
                key={tmpl.id}
                className={`card py-3 cursor-pointer transition-all ${
                  selected?.id === tmpl.id ? 'ring-2 ring-green-500' : 'hover:shadow-md'
                } ${!tmpl.ist_aktiv ? 'opacity-50' : ''}`}
                onClick={() => setSelected(selected?.id === tmpl.id ? null : tmpl)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900">{tmpl.name}</span>
                      {tmpl.typ && (
                        <span className="badge bg-green-50 text-green-700 text-xs">
                          {TYP_LABELS[tmpl.typ] ?? tmpl.typ}
                        </span>
                      )}
                      {!tmpl.ist_aktiv && (
                        <span className="badge bg-gray-100 text-gray-400 text-xs">Inaktiv</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{tmpl.betreff}</p>
                    {tmpl.verzoegerung_tage > 0 && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        Verzögerung: +{tmpl.verzoegerung_tage} Tage
                      </p>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <button
                      className="p-1.5 text-gray-400 hover:text-green-600 rounded"
                      onClick={(e) => { e.stopPropagation(); handlePreview(tmpl) }}
                      title="Vorschau"
                    >
                      <Eye size={15} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Edit panel */}
        {selected && (
          <TemplateEditPanel
            template={selected}
            onClose={() => setSelected(null)}
            onSaved={() => {
              qc.invalidateQueries({ queryKey: ['email-templates'] })
              setSelected(null)
              toast.success('Gespeichert')
            }}
            onDelete={() => deleteMutation.mutate(selected.id)}
          />
        )}
      </div>

      {/* Create modal */}
      {showCreate && (
        <TemplateModal
          onClose={() => setShowCreate(false)}
          onSaved={() => {
            qc.invalidateQueries({ queryKey: ['email-templates'] })
            setShowCreate(false)
            toast.success('Template erstellt')
          }}
        />
      )}

      {/* Preview modal */}
      {previewHtml && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">E-Mail-Vorschau</h2>
              <button onClick={() => setPreviewHtml(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div
              className="flex-1 overflow-auto p-4"
              dangerouslySetInnerHTML={{ __html: previewHtml }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function TemplateEditPanel({
  template,
  onClose,
  onSaved,
  onDelete,
}: {
  template: EmailTemplate
  onClose: () => void
  onSaved: () => void
  onDelete: () => void
}) {
  const [form, setForm] = useState({
    name: template.name,
    betreff: template.betreff,
    html_inhalt: template.html_inhalt,
    text_inhalt: template.text_inhalt ?? '',
    typ: template.typ ?? '',
    reihenfolge: template.reihenfolge,
    verzoegerung_tage: template.verzoegerung_tage,
    beschreibung: template.beschreibung ?? '',
  })

  const updateMutation = useMutation({
    mutationFn: (data: unknown) => emailTemplatesApi.update(template.id, data),
    onSuccess: onSaved,
    onError: () => toast.error('Fehler beim Speichern'),
  })

  return (
    <div className="w-1/2 card flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Template bearbeiten</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X size={18} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto space-y-3">
        <div>
          <label className="label">Name</label>
          <input className="input text-sm" value={form.name}
            onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>
        <div>
          <label className="label">Betreff</label>
          <input className="input text-sm" value={form.betreff}
            onChange={(e) => setForm(f => ({ ...f, betreff: e.target.value }))} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Typ</label>
            <select className="input text-sm" value={form.typ}
              onChange={(e) => setForm(f => ({ ...f, typ: e.target.value }))}>
              <option value="">Sonstige</option>
              {Object.entries(TYP_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Reihenfolge</label>
            <input type="number" className="input text-sm" value={form.reihenfolge}
              onChange={(e) => setForm(f => ({ ...f, reihenfolge: Number(e.target.value) }))} />
          </div>
        </div>
        <div>
          <label className="label">Verzögerung (Tage nach vorheriger Mail)</label>
          <input type="number" className="input text-sm" value={form.verzoegerung_tage}
            onChange={(e) => setForm(f => ({ ...f, verzoegerung_tage: Number(e.target.value) }))} />
        </div>
        <div>
          <label className="label">HTML-Inhalt</label>
          <textarea
            className="input h-48 resize-none text-xs font-mono"
            value={form.html_inhalt}
            onChange={(e) => setForm(f => ({ ...f, html_inhalt: e.target.value }))}
          />
        </div>
        <div>
          <label className="label">Text-Inhalt (Fallback)</label>
          <textarea
            className="input h-24 resize-none text-xs font-mono"
            value={form.text_inhalt}
            onChange={(e) => setForm(f => ({ ...f, text_inhalt: e.target.value }))}
          />
        </div>
      </div>
      <div className="flex justify-between pt-4 border-t mt-4">
        <button
          className="btn-secondary text-red-600 hover:bg-red-50 text-sm"
          onClick={onDelete}
        >
          Deaktivieren
        </button>
        <div className="flex gap-2">
          <button className="btn-secondary text-sm" onClick={onClose}>Abbrechen</button>
          <button
            className="btn-primary text-sm"
            onClick={() => updateMutation.mutate(form)}
            disabled={updateMutation.isPending}
          >
            <Check size={15} />
            {updateMutation.isPending ? 'Speichern…' : 'Speichern'}
          </button>
        </div>
      </div>
    </div>
  )
}

function TemplateModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    name: '',
    betreff: '',
    html_inhalt: '',
    text_inhalt: '',
    typ: 'onboarding_welcome',
    reihenfolge: 0,
    verzoegerung_tage: 0,
  })

  const createMutation = useMutation({
    mutationFn: (data: unknown) => emailTemplatesApi.create(data),
    onSuccess: onSaved,
    onError: () => toast.error('Fehler beim Erstellen'),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Neues E-Mail-Template</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">×</button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          <div>
            <label className="label">Name *</label>
            <input className="input" required value={form.name}
              onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div>
            <label className="label">Betreff *</label>
            <input className="input" required value={form.betreff}
              onChange={(e) => setForm(f => ({ ...f, betreff: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Typ</label>
              <select className="input" value={form.typ}
                onChange={(e) => setForm(f => ({ ...f, typ: e.target.value }))}>
                {Object.entries(TYP_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Reihenfolge</label>
              <input type="number" className="input" value={form.reihenfolge}
                onChange={(e) => setForm(f => ({ ...f, reihenfolge: Number(e.target.value) }))} />
            </div>
          </div>
          <div>
            <label className="label">Verzögerung (Tage)</label>
            <input type="number" className="input" value={form.verzoegerung_tage}
              onChange={(e) => setForm(f => ({ ...f, verzoegerung_tage: Number(e.target.value) }))} />
          </div>
          <div>
            <label className="label">HTML-Inhalt *</label>
            <textarea
              className="input h-48 resize-none text-xs font-mono"
              required
              value={form.html_inhalt}
              onChange={(e) => setForm(f => ({ ...f, html_inhalt: e.target.value }))}
              placeholder="<p>Sehr geehrte/r {{Ansprechpartner}},</p>..."
            />
          </div>
          <div>
            <label className="label">Text-Inhalt (Fallback)</label>
            <textarea
              className="input h-20 resize-none text-xs font-mono"
              value={form.text_inhalt}
              onChange={(e) => setForm(f => ({ ...f, text_inhalt: e.target.value }))}
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 px-6 py-4 border-t">
          <button className="btn-secondary" onClick={onClose}>Abbrechen</button>
          <button
            className="btn-primary"
            disabled={!form.name || !form.betreff || !form.html_inhalt || createMutation.isPending}
            onClick={() => createMutation.mutate(form)}
          >
            {createMutation.isPending ? 'Erstellen…' : 'Template erstellen'}
          </button>
        </div>
      </div>
    </div>
  )
}
