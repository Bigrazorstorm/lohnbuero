import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, MessageSquare, Search } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { ticketsApi, mandantenApi } from '../api/client'
import type { Ticket, TicketStatus, Mandant, TicketKommentar } from '../types'
import { TicketStatusBadge, PrioritaetBadge } from '../components/StatusBadge'
import { useAuthStore } from '../store/auth'

export default function Tickets() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Ticket | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const { data: tickets = [], isLoading } = useQuery<Ticket[]>({
    queryKey: ['tickets', { status: statusFilter }],
    queryFn: () =>
      ticketsApi.list(statusFilter ? { status: statusFilter } : {}).then((r) => (r as { data: Ticket[] }).data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: unknown }) => ticketsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tickets'] })
      toast.success('Gespeichert')
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
          className="input w-48"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TicketStatus | '')}
        >
          <option value="">Alle Status</option>
          <option value="offen">Offen</option>
          <option value="in_bearbeitung">In Bearbeitung</option>
          <option value="beantwortet">Beantwortet</option>
          <option value="geschlossen">Geschlossen</option>
        </select>
      </div>

      {/* Count */}
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
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {ticket.mandant.name} · {format(new Date(ticket.created_at), 'dd.MM.yyyy', { locale: de })}
                    </p>
                  </div>
                  <TicketStatusBadge status={ticket.status} />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <TicketDetail
            ticket={selected}
            onUpdate={(data) => updateMutation.mutate({ id: selected.id, data })}
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
            setShowCreate(false)
            toast.success('Rückfrage erstellt')
          }}
        />
      )}
    </div>
  )
}

function TicketDetail({ ticket, onUpdate, onClose }: {
  ticket: Ticket; onUpdate: (data: unknown) => void; onClose: () => void
}) {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [kommentar, setKommentar] = useState('')

  const { data: detail } = useQuery<Ticket>({
    queryKey: ['ticket', ticket.id],
    queryFn: () => ticketsApi.get(ticket.id).then((r) => (r as { data: Ticket }).data),
  })

  const addKommentarMutation = useMutation({
    mutationFn: (inhalt: string) => ticketsApi.addKommentar(ticket.id, inhalt),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ticket', ticket.id] })
      qc.invalidateQueries({ queryKey: ['tickets'] })
      setKommentar('')
    },
    onError: () => toast.error('Fehler'),
  })

  const t = detail ?? ticket

  return (
    <div className="w-1/2 card flex flex-col max-h-[70vh]">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{t.titel}</h3>
          <p className="text-xs text-gray-400 mt-0.5">{t.mandant.name}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        <TicketStatusBadge status={t.status} />
        <PrioritaetBadge prioritaet={t.prioritaet} />
        {t.kategorie && <span className="badge bg-gray-100 text-gray-600">{t.kategorie}</span>}
      </div>

      {t.beschreibung && (
        <p className="text-sm text-gray-600 mb-3 p-3 bg-gray-50 rounded-lg">{t.beschreibung}</p>
      )}

      {/* Status change */}
      {user?.role !== 'mandant' && t.status !== 'geschlossen' && (
        <div className="flex gap-2 mb-3">
          <select
            className="input text-sm flex-1"
            value={t.status}
            onChange={(e) => onUpdate({ status: e.target.value })}
          >
            <option value="offen">Offen</option>
            <option value="in_bearbeitung">In Bearbeitung</option>
            <option value="beantwortet">Beantwortet</option>
            <option value="geschlossen">Schließen</option>
          </select>
        </div>
      )}

      {/* Kommentare */}
      <div className="flex-1 overflow-y-auto space-y-2 mb-3">
        <p className="text-xs font-semibold text-gray-500 uppercase">Verlauf</p>
        {t.kommentare.length === 0 ? (
          <p className="text-xs text-gray-400 italic">Noch keine Kommentare</p>
        ) : (
          t.kommentare.map((k: TicketKommentar) => (
            <div key={k.id} className={`text-sm p-2.5 rounded-lg ${k.autor.id === user?.id ? 'bg-blue-50 ml-4' : 'bg-gray-50 mr-4'}`}>
              <p className="text-xs font-medium text-gray-500 mb-0.5">{k.autor.full_name}</p>
              <p className="text-gray-800">{k.inhalt}</p>
              <p className="text-xs text-gray-400 mt-0.5">
                {format(new Date(k.created_at), 'dd.MM. HH:mm', { locale: de })}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Add comment */}
      {t.status !== 'geschlossen' && (
        <div className="flex gap-2 pt-3 border-t">
          <input
            className="input flex-1 text-sm"
            placeholder="Antwort schreiben…"
            value={kommentar}
            onChange={(e) => setKommentar(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && kommentar.trim()) {
                addKommentarMutation.mutate(kommentar.trim())
              }
            }}
          />
          <button
            className="btn-primary text-sm py-2"
            disabled={!kommentar.trim() || addKommentarMutation.isPending}
            onClick={() => addKommentarMutation.mutate(kommentar.trim())}
          >
            Senden
          </button>
        </div>
      )}
    </div>
  )
}

function CreateTicketModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { user } = useAuthStore()
  const [form, setForm] = useState({
    mandant_id: '',
    titel: '',
    beschreibung: '',
    prioritaet: 'normal',
    kategorie: '',
  })

  const { data: mandanten = [] } = useQuery<Mandant[]>({
    queryKey: ['mandanten'],
    queryFn: () => mandantenApi.list({ aktiv: true }).then((r) => (r as { data: Mandant[] }).data),
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
          <div>
            <label className="label">Mandant *</label>
            <select className="input" required value={form.mandant_id}
              onChange={e => setForm(f => ({ ...f, mandant_id: e.target.value }))}>
              <option value="">– auswählen –</option>
              {mandanten.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
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
                <option value="dringend">Dringend</option>
              </select>
            </div>
            <div>
              <label className="label">Kategorie</label>
              <input className="input" placeholder="z.B. Fehlende Unterlagen"
                value={form.kategorie}
                onChange={e => setForm(f => ({ ...f, kategorie: e.target.value }))} />
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
