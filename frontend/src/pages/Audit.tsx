import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Shield, Download, Filter } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { auditApi } from '../api/client'
import type { AuditLog } from '../types'

const OBJEKT_TYPEN = [
  'mandant', 'ticket', 'workflow', 'workflow_item',
  'email_template', 'email', 'dokument',
]

const AKTIONSTYPEN = [
  'erstellt', 'geaendert', 'archiviert', 'stammdaten_geaendert',
  'statuswechsel', 'generiert', 'bulk_generiert',
  'eskalation', 'kommentar', 'kommentar_intern', 'mandantenantwort',
  'versendet', 'onboarding_versendet', 'statusaenderung',
]

function jsonPretty(raw?: string): string {
  if (!raw) return '–'
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}

export default function Audit() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [expanded, setExpanded] = useState<number | null>(null)

  const { data: entries = [], isLoading, refetch } = useQuery<AuditLog[]>({
    queryKey: ['audit', filters],
    queryFn: () =>
      auditApi.list(Object.fromEntries(Object.entries(filters).filter(([, v]) => v)))
        .then((r) => (r as { data: AuditLog[] }).data),
  })

  const setFilter = (key: string, value: string) =>
    setFilters((f) => ({ ...f, [key]: value }))

  const handleExport = async () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    const res = await auditApi.exportCsv(params) as { data: Blob }
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-log-${format(new Date(), 'yyyy-MM-dd')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={22} className="text-indigo-600" />
          <h1 className="text-2xl font-bold text-gray-900">Audit-Log</h1>
        </div>
        <button className="btn-secondary flex items-center gap-2" onClick={handleExport}>
          <Download size={16} />
          CSV-Export
        </button>
      </div>

      {/* Filters */}
      <div className="card py-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter size={16} className="text-gray-400" />
          <span className="text-sm font-semibold text-gray-600">Filter</span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <div>
            <label className="label">Mandant-ID</label>
            <input
              type="number"
              className="input text-sm"
              placeholder="z.B. 1"
              value={filters.mandant_id || ''}
              onChange={(e) => setFilter('mandant_id', e.target.value)}
            />
          </div>
          <div>
            <label className="label">Objekt-Typ</label>
            <select
              className="input text-sm"
              value={filters.objekt_typ || ''}
              onChange={(e) => setFilter('objekt_typ', e.target.value)}
            >
              <option value="">Alle</option>
              {OBJEKT_TYPEN.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Aktionstyp</label>
            <select
              className="input text-sm"
              value={filters.aktionstyp || ''}
              onChange={(e) => setFilter('aktionstyp', e.target.value)}
            >
              <option value="">Alle</option>
              {AKTIONSTYPEN.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Von</label>
            <input
              type="datetime-local"
              className="input text-sm"
              value={filters.von || ''}
              onChange={(e) => setFilter('von', e.target.value)}
            />
          </div>
          <div>
            <label className="label">Bis</label>
            <input
              type="datetime-local"
              className="input text-sm"
              value={filters.bis || ''}
              onChange={(e) => setFilter('bis', e.target.value)}
            />
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <button className="btn-primary text-sm" onClick={() => refetch()}>
            Suchen
          </button>
          <button
            className="btn-secondary text-sm"
            onClick={() => setFilters({})}
          >
            Filter zurücksetzen
          </button>
        </div>
      </div>

      {/* Results count */}
      <p className="text-sm text-gray-500">
        {entries.length} Einträge {entries.length === 200 ? '(max. 200 – Filter einschränken)' : ''}
      </p>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="text-center py-12 text-gray-400">Laden…</div>
        ) : entries.length === 0 ? (
          <div className="text-center py-12">
            <Shield size={40} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-400">Keine Einträge gefunden</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Zeitstempel</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Objekt-Typ</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Objekt-ID</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktion</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Benutzer</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Beschreibung</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {entries.map((entry) => (
                  <>
                    <tr
                      key={entry.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                    >
                      <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap font-mono">
                        {format(new Date(entry.zeitstempel), 'dd.MM.yy HH:mm:ss', { locale: de })}
                      </td>
                      <td className="px-4 py-3">
                        <span className="badge bg-indigo-50 text-indigo-700 font-mono text-xs">
                          {entry.objekt_typ}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {entry.objekt_id ?? '–'}
                      </td>
                      <td className="px-4 py-3">
                        <span className="badge bg-gray-100 text-gray-700 font-mono text-xs">
                          {entry.aktionstyp}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {entry.benutzer_id ? (
                          <span>
                            ID {entry.benutzer_id}
                            {entry.benutzerrolle && (
                              <span className="ml-1 text-gray-400">({entry.benutzerrolle})</span>
                            )}
                          </span>
                        ) : (
                          <span className="text-gray-400">System</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-700 max-w-xs truncate">
                        {entry.beschreibung || '–'}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400">
                        {(entry.alter_wert || entry.neuer_wert) ? (
                          <span className="text-blue-500 hover:underline">Details</span>
                        ) : null}
                      </td>
                    </tr>
                    {expanded === entry.id && (entry.alter_wert || entry.neuer_wert) && (
                      <tr key={`${entry.id}-detail`} className="bg-gray-50">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs font-semibold text-gray-500 mb-1">Alter Wert</p>
                              <pre className="text-xs bg-white border rounded p-2 overflow-x-auto max-h-40">
                                {jsonPretty(entry.alter_wert)}
                              </pre>
                            </div>
                            <div>
                              <p className="text-xs font-semibold text-gray-500 mb-1">Neuer Wert</p>
                              <pre className="text-xs bg-white border rounded p-2 overflow-x-auto max-h-40">
                                {jsonPretty(entry.neuer_wert)}
                              </pre>
                            </div>
                          </div>
                          {entry.ip_adresse && (
                            <p className="text-xs text-gray-400 mt-2">IP: {entry.ip_adresse}</p>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
