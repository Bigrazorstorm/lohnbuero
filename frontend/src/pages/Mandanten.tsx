import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Building2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { mandantenApi, usersApi } from '../api/client'
import type { Mandant, User } from '../types'
import { KategorieBadge } from '../components/StatusBadge'
import MandantForm from './MandantForm'

export default function Mandanten() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)

  const { data: mandanten = [], isLoading } = useQuery<Mandant[]>({
    queryKey: ['mandanten'],
    queryFn: () => mandantenApi.list({ aktiv: true }).then((r) => (r as { data: Mandant[] }).data),
  })

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.list().then((r) => (r as { data: User[] }).data),
  })

  const createMutation = useMutation({
    mutationFn: (data: unknown) => mandantenApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mandanten'] })
      toast.success('Mandant angelegt')
      setShowForm(false)
    },
    onError: () => toast.error('Fehler beim Anlegen'),
  })

  const filtered = mandanten.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    (m.nummer ?? '').includes(search) ||
    (m.ansprechpartner_name ?? '').toLowerCase().includes(search.toLowerCase())
  )

  const sachbearbeiterList = users.filter(
    (u) => u.role === 'sachbearbeiter' || u.role === 'teamleitung'
  )

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Mandanten</h1>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          <Plus size={16} />
          Neuer Mandant
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Name, Nummer oder Ansprechpartner suchen…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Stats row */}
      <div className="flex gap-3 text-sm text-gray-500">
        <span>{filtered.length} Mandanten</span>
        <span>·</span>
        <span>{filtered.filter(m => m.kategorie === 'A').length} Klasse A</span>
        <span>·</span>
        <span>{filtered.filter(m => m.kategorie === 'B').length} Klasse B</span>
        <span>·</span>
        <span>{filtered.filter(m => m.kategorie === 'C').length} Klasse C</span>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="card text-center py-12 text-gray-400">Laden…</div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12">
          <Building2 size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-400">Keine Mandanten gefunden</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Mandant</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Klasse</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">MA</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Frist</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Abgabe</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Sachbearbeiter</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((m) => (
                <tr
                  key={m.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/mandanten/${m.id}`)}
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{m.name}</div>
                    <div className="text-xs text-gray-400">
                      {m.nummer && `#${m.nummer} · `}{m.branche ?? ''}
                    </div>
                  </td>
                  <td className="px-4 py-3"><KategorieBadge kategorie={m.kategorie} /></td>
                  <td className="px-4 py-3 text-gray-600">{m.mitarbeiteranzahl}</td>
                  <td className="px-4 py-3 text-gray-600">{m.lohnabschluss_tag}.</td>
                  <td className="px-4 py-3">
                    <span className="capitalize text-gray-600">{m.abgabeweg}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {m.sachbearbeiter?.full_name ?? <span className="text-gray-300">–</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create form modal */}
      {showForm && (
        <MandantForm
          sachbearbeiterList={sachbearbeiterList}
          onSubmit={(data) => createMutation.mutate(data)}
          onClose={() => setShowForm(false)}
          loading={createMutation.isPending}
        />
      )}
    </div>
  )
}
