import { useState, FormEvent } from 'react'
import { X } from 'lucide-react'
import type { User } from '../types'

interface Props {
  sachbearbeiterList: User[]
  onSubmit: (data: unknown) => void
  onClose: () => void
  loading?: boolean
  initial?: Record<string, unknown>
}

export default function MandantForm({ sachbearbeiterList, onSubmit, onClose, loading, initial }: Props) {
  const [form, setForm] = useState({
    name: '',
    nummer: '',
    branche: '',
    ansprechpartner_name: '',
    ansprechpartner_email: '',
    ansprechpartner_telefon: '',
    lohnabschluss_tag: 15,
    abgabeweg: 'email',
    kategorie: 'B',
    mitarbeiteranzahl: 1,
    besonderheiten: '',
    sachbearbeiter_id: '',
    vertretung_id: '',
    monatspauschale: '',
    ...initial,
  })

  const set = (k: string, v: unknown) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const payload: Record<string, unknown> = {
      ...form,
      lohnabschluss_tag: Number(form.lohnabschluss_tag),
      mitarbeiteranzahl: Number(form.mitarbeiteranzahl),
      sachbearbeiter_id: form.sachbearbeiter_id ? Number(form.sachbearbeiter_id) : null,
      vertretung_id: form.vertretung_id ? Number(form.vertretung_id) : null,
      monatspauschale: form.monatspauschale ? Number(form.monatspauschale) : null,
    }
    if (!payload.nummer) delete payload.nummer
    onSubmit(payload)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Neuer Mandant</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto px-6 py-5 space-y-4 flex-1">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="label">Name *</label>
              <input className="input" required value={form.name as string} onChange={e => set('name', e.target.value)} />
            </div>
            <div>
              <label className="label">Mandantennummer</label>
              <input className="input" value={form.nummer as string} onChange={e => set('nummer', e.target.value)} />
            </div>
            <div>
              <label className="label">Branche</label>
              <input className="input" value={form.branche as string} onChange={e => set('branche', e.target.value)} />
            </div>
            <div>
              <label className="label">Ansprechpartner Name</label>
              <input className="input" value={form.ansprechpartner_name as string} onChange={e => set('ansprechpartner_name', e.target.value)} />
            </div>
            <div>
              <label className="label">E-Mail Ansprechpartner</label>
              <input type="email" className="input" value={form.ansprechpartner_email as string} onChange={e => set('ansprechpartner_email', e.target.value)} />
            </div>
            <div>
              <label className="label">Telefon</label>
              <input className="input" value={form.ansprechpartner_telefon as string} onChange={e => set('ansprechpartner_telefon', e.target.value)} />
            </div>
            <div>
              <label className="label">Kategorie</label>
              <select className="input" value={form.kategorie as string} onChange={e => set('kategorie', e.target.value)}>
                <option value="A">A – Premium</option>
                <option value="B">B – Standard</option>
                <option value="C">C – Basis</option>
              </select>
            </div>
            <div>
              <label className="label">Abgabeweg</label>
              <select className="input" value={form.abgabeweg as string} onChange={e => set('abgabeweg', e.target.value)}>
                <option value="email">E-Mail</option>
                <option value="portal">Portal</option>
                <option value="post">Post</option>
                <option value="fax">Fax</option>
              </select>
            </div>
            <div>
              <label className="label">Lohnabschluss Tag (im Monat)</label>
              <input type="number" min={1} max={28} className="input" value={form.lohnabschluss_tag as number}
                onChange={e => set('lohnabschluss_tag', e.target.value)} />
            </div>
            <div>
              <label className="label">Mitarbeiteranzahl</label>
              <input type="number" min={1} className="input" value={form.mitarbeiteranzahl as number}
                onChange={e => set('mitarbeiteranzahl', e.target.value)} />
            </div>
            <div>
              <label className="label">Sachbearbeiter</label>
              <select className="input" value={form.sachbearbeiter_id as string} onChange={e => set('sachbearbeiter_id', e.target.value)}>
                <option value="">– kein –</option>
                {sachbearbeiterList.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Vertretung</label>
              <select className="input" value={form.vertretung_id as string} onChange={e => set('vertretung_id', e.target.value)}>
                <option value="">– kein –</option>
                {sachbearbeiterList.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Monatspauschale (€)</label>
              <input type="number" step="0.01" className="input" value={form.monatspauschale as string}
                onChange={e => set('monatspauschale', e.target.value)} />
            </div>
            <div className="col-span-2">
              <label className="label">Besonderheiten / Notizen</label>
              <textarea className="input h-20 resize-none" value={form.besonderheiten as string}
                onChange={e => set('besonderheiten', e.target.value)} />
            </div>
          </div>
        </form>

        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button type="button" className="btn-secondary" onClick={onClose}>Abbrechen</button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            onClick={(e) => {
              const form = (e.currentTarget.closest('.fixed') as HTMLElement).querySelector('form')
              form?.requestSubmit()
            }}
          >
            {loading ? 'Speichern…' : 'Mandant anlegen'}
          </button>
        </div>
      </div>
    </div>
  )
}
