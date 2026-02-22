import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, MessageSquare, Search, AlertTriangle, Lock, Globe, ChevronUp } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { ticketsApi, mandantenApi } from '../api/client'
import type { Ticket, TicketStatus, Mandant, TicketKommentar, TicketKPIs } from '../types'
import { TicketStatusBadge, PrioritaetBadge } from '../components/StatusBadge'
import { useAuthStore } from '../store/auth'

const STATUS_LABELS: Record<TicketStatus, string> = {
  neu: 'Neu',
  offen: 'Offen',
  in_bearbeitung: 'In Bearbeitung',
  wartet_auf_mandant: 'Wartet auf Mandant',
  intern_in_klaerung: 'Intern in Klärung',
  beantwortet: 'Beantwortet',
  geloest: 'Gelöst',
  geschlossen: 'Geschlossen',
}

const KATEGORIE_OPTIONS = [
  'Eintritt',
  'Austritt',
  'Fehlzeit',
  'Abrechnungsfehler',
  'Fehlende Unterlagen',
  'Sonstiges',
]

export default function Tickets() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Ticket | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const isMandant = user?.role === 'mandant'
  const isStaff = !isMandant

  const { data: tickets = [], isLoading } = useQuery<Ticket[]>({
    queryKey: ['tickets', { status: statusFilter }],
    queryFn: () =>
      ticketsApi.list(statusFilter ? { status: statusFilter } : {}).then((r) => (r as { data: Ticket[] }).data),
  })

  const { data: kpis } = useQuery<TicketKPIs>({
    queryKey: ['ticket-kpis'],
    queryFn: () => ticketsApi.kpis().then((r) => (r as { data: TicketKPIs }).data),
    enabled: isStaff,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: unknown }) => ticketsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tickets'] })
      qc.invalidateQueries({ queryKey: ['ticket-kpis'] })
      toast.success('Gespeichert')
    },
  })

  const eskaliertMutation = useMutation({
    mutationFn: (id: number) => ticketsApi.eskalieren(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tickets'] })
      qc.invalidateQueries({ queryKey: ['ticket-kpis'] })
      toast.success('Ticket eskaliert')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      toast.error(msg ?? 'Eskalation fehlgeschlagen')
    },
  })

  const filtered = tickets.filter(
    (t) =>
      t.titel.toLowerCase().includes(search.toLowerCase()) ||
      t.mandant.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Rückfragen & Tickets</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} />
          Neue Rückfrage
        </button>
      </div>

      {/* KPI strip (staff only) */}
      {isStaff && kpis && (
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: 'Gesamt', value: kpis.gesamt, color: 'text-gray-700' },
            { label: 'Offen', value: kpis.offen, color: 'text-blue-600' },
            { label: 'Eskaliert', value: kpis.eskaliert, color: 'text-orange-600' },
            { label: 'Kritisch offen', value: kpis.kritisch_offen, color: 'text-red-600' },
            {
              label: 'Ø Antwortzeit',
              value: kpis.avg_antwortzeit_stunden != null
                ? `${kpis.avg_antwortzeit_stunden}h`
                : '–',
              color: 'text-purple-600',
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="card py-3 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Suchen…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="input w-52"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TicketStatus | '')}
        >
          <option value="">Alle Status</option>
          {(Object.entries(STATUS_LABELS) as [TicketStatus, string][]).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <p className="text-sm text-gray-500">{filtered.length} Tickets</p>

      {/* Main layout */}
      <div className="flex gap-5">
        {/* List */}
        <div className={`${selected ? 'w-1/2' : 'w-full'} space-y-2`}>
          {isLoading ? (
            <div className="card text-center py-12 text-gray-400">Laden…</div>
          ) : filtered.length === 0 ? (
            <div className="card text-center py-12">
              <MessageSquare size={40} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-400">Keine Tickets</p>
            </div>
          ) : (
            filtered.map((ticket) => (
              <div
                key={ticket.id}
                className={`card py-3 cursor-pointer transition-all ${
                  selected?.id === ticket.id ? 'ring-2 ring-blue-500' : 'hover:shadow-md'
                }`}
                onClick={() => setSelected(ticket.id === selected?.id ? null : ticket)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900 truncate">{ticket.titel}</span>
                      <PrioritaetBadge prioritaet={ticket.prioritaet} />
                      {ticket.eskalationsstufe && (
                        <span className="badge bg-orange-100 text-orange-700 text-xs flex items-center gap-1">
                          <ChevronUp size={10} />
                          {ticket.eskalationsstufe === 'teamleitung' ? 'TL' : 'Leitung'}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {ticket.mandant.name}
                      {ticket.kategorie && ` · ${ticket.kategorie}`}
                      {ticket.monat && ticket.jahr && ` · ${ticket.monat}/${ticket.jahr}`}
                      {` · ${format(new Date(ticket.created_at), 'dd.MM.yyyy', { locale: de })}`}
                    </p>
                  </div>
                  <TicketStatusBadge status={ticket.status} />
                </div>
                {/* SLA warning */}
                {ticket.faellig_bis && ticket.status !== 'geschlossen' && ticket.status !== 'geloest' && (
                  (() => {
                    const overdue = new Date(ticket.faellig_bis) < new Date()
                    return overdue ? (
                      <p className="text-xs text-red-500 mt-1.5 flex items-center gap-1">
                        <AlertTriangle size={11} />
                        SLA überschritten: {format(new Date(ticket.faellig_bis), 'dd.MM. HH:mm', { locale: de })}
                      </p>
                    ) : null
                  })()
                )}
              </div>
            ))
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <TicketDetail
            ticket={selected}
            onUpdate={(data) => updateMutation.mutate({ id: selected.id, data })}
            onEskalieren={() => eskaliertMutation.mutate(selected.id)}
            onClose={() => setSelected(null)}
          />
        )}
      </div>

      {/* Create modal */}
      {showCreate && (
        <CreateTicketModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            qc.invalidateQueries({ queryKey: ['tickets'] })
            qc.invalidateQueries({ queryKey: ['ticket-kpis'] })
            setShowCreate(false)
            toast.success('Rückfrage erstellt')
          }}
        />
      )}
    </div>
  )
}

function TicketDetail({ ticket, onUpdate, onEskalieren, onClose }: {
  ticket: Ticket
  onUpdate: (data: unknown) => void
  onEskalieren: () => void
  onClose: () => void
}) {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isMandant = user?.role === 'mandant'
  const [kommentar, setKommentar] = useState('')
  const [istIntern, setIstIntern] = useState(false)

  const { data: detail } = useQuery<Ticket>({
    queryKey: ['ticket', ticket.id],
    queryFn: () => ticketsApi.get(ticket.id).then((r) => (r as { data: Ticket }).data),
  })

  const addKommentarMutation = useMutation({
    mutationFn: ({ inhalt, intern }: { inhalt: string; intern: boolean }) =>
      ticketsApi.addKommentar(ticket.id, inhalt, intern),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ticket', ticket.id] })
      qc.invalidateQueries({ queryKey: ['tickets'] })
      setKommentar('')
      setIstIntern(false)
    },
    onError: () => toast.error('Fehler'),
  })

  const t = detail ?? ticket

  const canEskalieren = !isMandant && t.status !== 'geschlossen' && t.status !== 'geloest' && t.eskalationsstufe !== 'leitung'

  return (
    <div className="w-1/2 card flex flex-col max-h-[80vh]">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{t.titel}</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {t.mandant.name}
            {t.kategorie && ` · ${t.kategorie}`}
            {t.monat && t.jahr && ` · ${t.monat}/${t.jahr}`}
          </p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        <TicketStatusBadge status={t.status} />
        <PrioritaetBadge prioritaet={t.prioritaet} />
        {t.eskalationsstufe && (
          <span className="badge bg-orange-100 text-orange-700 text-xs">
            Eskaliert: {t.eskalationsstufe === 'teamleitung' ? 'Teamleitung' : 'Kanzleileitung'}
          </span>
        )}
        {t.faellig_bis && (
          <span className={`badge text-xs ${new Date(t.faellig_bis) < new Date() ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
            SLA: {format(new Date(t.faellig_bis), 'dd.MM. HH:mm', { locale: de })}
          </span>
        )}
      </div>

      {t.beschreibung && (
        <p className="text-sm text-gray-600 mb-3 p-3 bg-gray-50 rounded-lg">{t.beschreibung}</p>
      )}

      {/* Status change (staff only) */}
      {!isMandant && t.status !== 'geschlossen' && (
        <div className="flex gap-2 mb-3">
          <select
            className="input text-sm flex-1"
            value={t.status}
            onChange={(e) => onUpdate({ status: e.target.value })}
          >
            {(Object.entries(STATUS_LABELS) as [TicketStatus, string][]).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          {canEskalieren && (
            <button
              className="btn-secondary text-sm px-3 text-orange-600 hover:bg-orange-50 border-orange-200"
              onClick={onEskalieren}
              title="Ticket eskalieren"
            >
              <ChevronUp size={15} />
            </button>
          )}
        </div>
      )}

      {/* Kommentare thread */}
      <div className="flex-1 overflow-y-auto space-y-2 mb-3">
        <p className="text-xs font-semibold text-gray-500 uppercase">Verlauf</p>
        {t.kommentare.length === 0 ? (
          <p className="text-xs text-gray-400 italic">Noch keine Kommentare</p>
        ) : (
          t.kommentare.map((k: TicketKommentar) => {
            const isOwn = k.autor.id === user?.id
            const isIntern = k.ist_intern
            return (
              <div
                key={k.id}
                className={`text-sm p-2.5 rounded-lg border ${
                  isIntern
                    ? 'bg-amber-50 border-amber-200'
                    : isOwn
                    ? 'bg-blue-50 border-blue-100 ml-4'
                    : 'bg-gray-50 border-gray-100 mr-4'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-xs font-medium text-gray-600">{k.autor.full_name}</span>
                  {isIntern ? (
                    <span className="flex items-center gap-0.5 text-xs text-amber-600 font-medium">
                      <Lock size={10} /> Intern
                    </span>
                  ) : (
                    <span className="flex items-center gap-0.5 text-xs text-gray-400">
                      <Globe size={10} />
                    </span>
                  )}
                </div>
                <p className="text-gray-800">{k.inhalt}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {format(new Date(k.created_at), 'dd.MM. HH:mm', { locale: de })}
                </p>
              </div>
            )
          })
        )}
      </div>

      {/* Add comment */}
      {t.status !== 'geschlossen' && (
        <div className="pt-3 border-t space-y-2">
          {/* Internal toggle (staff only) */}
          {!isMandant && (
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <div
                className={`w-8 h-4 rounded-full transition-colors relative ${istIntern ? 'bg-amber-500' : 'bg-gray-200'}`}
                onClick={() => setIstIntern(!istIntern)}
              >
                <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${istIntern ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                {istIntern ? <><Lock size={11} className="text-amber-500" /> Intern (nicht sichtbar für Mandant)</> : <><Globe size={11} /> Extern (sichtbar für Mandant)</>}
              </span>
            </label>
          )}
          <div className="flex gap-2">
            <input
              className="input flex-1 text-sm"
              placeholder={istIntern ? 'Interne Notiz…' : 'Antwort schreiben…'}
              value={kommentar}
              onChange={(e) => setKommentar(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && kommentar.trim()) {
                  addKommentarMutation.mutate({ inhalt: kommentar.trim(), intern: istIntern })
                }
              }}
            />
            <button
              className={`text-sm py-2 px-4 rounded-lg font-medium transition-colors ${
                istIntern
                  ? 'bg-amber-500 hover:bg-amber-600 text-white'
                  : 'btn-primary'
              }`}
              disabled={!kommentar.trim() || addKommentarMutation.isPending}
              onClick={() => addKommentarMutation.mutate({ inhalt: kommentar.trim(), intern: istIntern })}
            >
              Senden
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function CreateTicketModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { user } = useAuthStore()
  const isMandant = user?.role === 'mandant'
  const [form, setForm] = useState({
    mandant_id: '',
    titel: '',
    beschreibung: '',
    prioritaet: 'normal',
    kategorie: '',
    monat: '',
    jahr: '',
  })

  const { data: mandanten = [] } = useQuery<Mandant[]>({
    queryKey: ['mandanten'],
    queryFn: () => mandantenApi.list({ aktiv: true }).then((r) => (r as { data: Mandant[] }).data),
    enabled: !isMandant,
  })

  const createMutation = useMutation({
    mutationFn: (data: unknown) => ticketsApi.create(data),
    onSuccess: onCreated,
    onError: () => toast.error('Fehler beim Erstellen'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      ...form,
      mandant_id: Number(form.mandant_id),
      monat: form.monat ? Number(form.monat) : undefined,
      jahr: form.jahr ? Number(form.jahr) : undefined,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Neue Rückfrage</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">×</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {!isMandant && (
            <div>
              <label className="label">Mandant *</label>
              <select className="input" required value={form.mandant_id}
                onChange={e => setForm(f => ({ ...f, mandant_id: e.target.value }))}>
                <option value="">– auswählen –</option>
                {mandanten.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="label">Betreff *</label>
            <input className="input" required value={form.titel}
              onChange={e => setForm(f => ({ ...f, titel: e.target.value }))} />
          </div>
          <div>
            <label className="label">Beschreibung</label>
            <textarea className="input h-24 resize-none" value={form.beschreibung}
              onChange={e => setForm(f => ({ ...f, beschreibung: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Priorität</label>
              <select className="input" value={form.prioritaet}
                onChange={e => setForm(f => ({ ...f, prioritaet: e.target.value }))}>
                <option value="niedrig">Niedrig</option>
                <option value="normal">Normal</option>
                <option value="hoch">Hoch</option>
                <option value="kritisch">Kritisch</option>
              </select>
            </div>
            <div>
              <label className="label">Kategorie</label>
              <select className="input" value={form.kategorie}
                onChange={e => setForm(f => ({ ...f, kategorie: e.target.value }))}>
                <option value="">– auswählen –</option>
                {KATEGORIE_OPTIONS.map(k => <option key={k} value={k}>{k}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Monat (Lohnmonat)</label>
              <select className="input" value={form.monat}
                onChange={e => setForm(f => ({ ...f, monat: e.target.value }))}>
                <option value="">–</option>
                {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Jahr</label>
              <input
                type="number"
                className="input"
                placeholder={String(new Date().getFullYear())}
                value={form.jahr}
                onChange={e => setForm(f => ({ ...f, jahr: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" className="btn-secondary" onClick={onClose}>Abbrechen</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Erstellen…' : 'Rückfrage erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
