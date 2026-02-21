import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Building2, CheckSquare, AlertTriangle, MessageSquare,
  TrendingUp, Users, Clock
} from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { dashboardApi } from '../api/client'
import type { DashboardStats, MandantAmpelInfo } from '../types'
import Ampel from '../components/Ampel'
import { WorkflowStatusBadge } from '../components/StatusBadge'

export default function Dashboard() {
  const navigate = useNavigate()
  const now = new Date()

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.stats().then((r) => (r as { data: DashboardStats }).data),
    refetchInterval: 60_000,
  })

  const { data: ampelData } = useQuery<MandantAmpelInfo[]>({
    queryKey: ['dashboard-ampel'],
    queryFn: () => dashboardApi.ampel().then((r) => (r as { data: MandantAmpelInfo[] }).data),
    refetchInterval: 60_000,
  })

  const monatLabel = format(now, 'MMMM yyyy', { locale: de })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-0.5">Übersicht · {monatLabel}</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Mandanten aktiv"
          value={stats?.mandanten_aktiv ?? '–'}
          sub={`von ${stats?.mandanten_gesamt ?? '–'} gesamt`}
          icon={<Building2 size={20} />}
          color="blue"
        />
        <KpiCard
          label="Workflows offen"
          value={(stats?.workflows_offen ?? 0) + (stats?.workflows_in_bearbeitung ?? 0)}
          sub={`${stats?.workflows_eskaliert ?? 0} eskaliert`}
          icon={<CheckSquare size={20} />}
          color="indigo"
        />
        <KpiCard
          label="Offene Rückfragen"
          value={stats?.tickets_offen ?? '–'}
          sub={`${stats?.tickets_dringend ?? 0} dringend`}
          icon={<MessageSquare size={20} />}
          color="orange"
        />
        <div className="card flex flex-col gap-3">
          <p className="text-sm font-medium text-gray-500 flex items-center gap-2">
            <AlertTriangle size={16} className="text-gray-400" />
            Ampel
          </p>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-xl font-bold text-gray-900">{stats?.ampel_gruen ?? 0}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-yellow-400" />
              <span className="text-xl font-bold text-gray-900">{stats?.ampel_gelb ?? 0}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-xl font-bold text-gray-900">{stats?.ampel_rot ?? 0}</span>
            </div>
          </div>
          <p className="text-xs text-gray-400">Aktueller Monat</p>
        </div>
      </div>

      {/* Ampel Overview */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-gray-900">Mandanten-Ampel · {monatLabel}</h2>
          <span className="text-xs text-gray-400">{ampelData?.length ?? 0} Mandanten</span>
        </div>

        {/* Sort by ampel (rot first) */}
        {(() => {
          const sorted = [...(ampelData ?? [])].sort((a, b) => {
            const order = { rot: 0, gelb: 1, gruen: 2 }
            return order[a.ampelstatus] - order[b.ampelstatus]
          })

          if (sorted.length === 0) {
            return <p className="text-sm text-gray-400 py-4 text-center">Keine Mandanten vorhanden</p>
          }

          return (
            <div className="space-y-2">
              {sorted.map((item) => (
                <div
                  key={item.mandant_id}
                  className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => item.workflow_id
                    ? navigate(`/workflows/${item.workflow_id}`)
                    : navigate(`/mandanten/${item.mandant_id}`)
                  }
                >
                  <div className="flex items-center gap-3">
                    <Ampel status={item.ampelstatus} size="md" />
                    <div>
                      <span className="text-sm font-medium text-gray-900">{item.mandant_name}</span>
                      <span className="ml-2 text-xs text-gray-400">Klasse {item.mandant_kategorie}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {item.sachbearbeiter && (
                      <span className="text-xs text-gray-500">{item.sachbearbeiter.full_name}</span>
                    )}
                    {item.status && <WorkflowStatusBadge status={item.status} />}
                    {!item.workflow_id && (
                      <span className="badge bg-gray-100 text-gray-500">Kein Workflow</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )
        })()}
      </div>
    </div>
  )
}

function KpiCard({
  label, value, sub, icon, color
}: {
  label: string; value: number | string; sub: string; icon: React.ReactNode; color: string
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    orange: 'bg-orange-50 text-orange-600',
    green: 'bg-green-50 text-green-600',
  }
  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <span className={`p-2 rounded-lg ${colors[color]}`}>{icon}</span>
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
      </div>
    </div>
  )
}
