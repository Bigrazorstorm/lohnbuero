import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { CheckSquare, Search } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { workflowsApi } from '../api/client'
import type { WorkflowInstanzShort, WorkflowStatus } from '../types'
import Ampel from '../components/Ampel'
import { WorkflowStatusBadge, KategorieBadge } from '../components/StatusBadge'

const MONTHS = [
  'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
  'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'
]

export default function Workflows() {
  const navigate = useNavigate()
  const now = new Date()
  const [monat, setMonat] = useState(now.getMonth() + 1)
  const [jahr, setJahr] = useState(now.getFullYear())
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | ''>('')
  const [search, setSearch] = useState('')

  const { data: workflows = [], isLoading } = useQuery<WorkflowInstanzShort[]>({
    queryKey: ['workflows', { monat, jahr, status: statusFilter }],
    queryFn: () =>
      workflowsApi.list({
        monat,
        jahr,
        ...(statusFilter ? { status: statusFilter } : {}),
      }).then((r) => (r as { data: WorkflowInstanzShort[] }).data),
  })

  const filtered = workflows.filter((wf) =>
    (wf.mandant?.name ?? '').toLowerCase().includes(search.toLowerCase())
  )

  const years = [now.getFullYear() - 1, now.getFullYear(), now.getFullYear() + 1]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
        <div className="flex items-center gap-2 text-sm">
          <select
            className="input w-auto"
            value={monat}
            onChange={(e) => setMonat(Number(e.target.value))}
          >
            {MONTHS.map((m, i) => (
              <option key={i} value={i + 1}>{m}</option>
            ))}
          </select>
          <select
            className="input w-auto"
            value={jahr}
            onChange={(e) => setJahr(Number(e.target.value))}
          >
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Mandant suchen…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="input w-48"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as WorkflowStatus | '')}
        >
          <option value="">Alle Status</option>
          <option value="offen">Offen</option>
          <option value="in_bearbeitung">In Bearbeitung</option>
          <option value="warte_freigabe">Warte Freigabe</option>
          <option value="eskaliert">Eskaliert</option>
          <option value="abgeschlossen">Abgeschlossen</option>
        </select>
      </div>

      {/* Ampel summary */}
      <div className="grid grid-cols-3 gap-3">
        {(['rot', 'gelb', 'gruen'] as const).map((a) => {
          const count = filtered.filter(w => w.ampelstatus === a).length
          const colors = { rot: 'border-red-200 bg-red-50', gelb: 'border-yellow-200 bg-yellow-50', gruen: 'border-green-200 bg-green-50' }
          const labels = { rot: 'Überfällig', gelb: 'Warnung', gruen: 'Pünktlich' }
          const text = { rot: 'text-red-700', gelb: 'text-yellow-700', gruen: 'text-green-700' }
          return (
            <div key={a} className={`rounded-lg border p-3 flex items-center gap-3 ${colors[a]}`}>
              <Ampel status={a} size="lg" />
              <div>
                <p className={`text-xl font-bold ${text[a]}`}>{count}</p>
                <p className={`text-xs ${text[a]}`}>{labels[a]}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="card text-center py-12 text-gray-400">Laden…</div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12">
          <CheckSquare size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-400">Keine Workflows für {MONTHS[monat - 1]} {jahr}</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Ampel</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Mandant</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Monat</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((wf) => (
                <tr
                  key={wf.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/workflows/${wf.id}`)}
                >
                  <td className="px-4 py-3">
                    <Ampel status={wf.ampelstatus} size="md" showLabel />
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-gray-900">{wf.mandant?.name ?? '–'}</span>
                    {wf.mandant && (
                      <span className="ml-2"><KategorieBadge kategorie={wf.mandant.kategorie} /></span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {format(new Date(wf.jahr, wf.monat - 1, 1), 'MMMM yyyy', { locale: de })}
                  </td>
                  <td className="px-4 py-3">
                    <WorkflowStatusBadge status={wf.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
