import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Building2, CheckSquare, AlertTriangle, MessageSquare,
  Clock, PlayCircle, PauseCircle, CheckCircle2, AlertCircle,
  Send, Mail, FileCheck, ArrowRight
} from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { dashboardApi } from '../api/client'
import { ticketsApi } from '../api/client'
import type { DashboardMeinTag, DashboardStats, KritischInfo, MeineArbeitItem, WartetAufMandantInfo } from '../types'
import Ampel from '../components/Ampel'
import { WorkflowStatusBadge, PrioritaetBadge } from '../components/StatusBadge'
import { useState } from 'react'

export default function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const now = new Date()
  const monatLabel = format(now, 'MMMM yyyy', { locale: de })

  // Fetch stats (for KPI cards)
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.stats().then((r) => (r as { data: DashboardStats }).data),
    refetchInterval: 60_000,
  })

  // Fetch "Mein Tag" data
  const { data: meinTag, isLoading: meinTagLoading } = useQuery<DashboardMeinTag>({
    queryKey: ['dashboard-mein-tag'],
    queryFn: () => dashboardApi.meinTag().then((r) => (r as { data: DashboardMeinTag }).data),
    refetchInterval: 60_000,
  })

  // Quick action: Reminder (placeholder - would open a modal in full implementation)
  const [reminderSent, setReminderSent] = useState<number | null>(null)
  
  // Quick action: Answer ticket (navigate to ticket)
  const handleAnswerTicket = (ticketId: number) => {
    navigate(`/tickets/${ticketId}`)
  }

  // Quick action: Complete step (would open a dialog in full implementation)
  const handleCompleteStep = (item: MeineArbeitItem) => {
    if (item.typ === 'workflow_schritt') {
      // Navigate to workflow detail with step highlighted
      navigate(`/workflows/${item.mandant_id}?step=${item.id}`)
    } else {
      // Navigate to sonderaufgabe detail
      navigate(`/sonderaufgaben/${item.id}`)
    }
  }

  // Format date for display
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    try {
      return format(new Date(dateStr), 'dd.MM.', { locale: de })
    } catch {
      return dateStr
    }
  }

  // Get urgency color based on days until deadline
  const getUrgencyColor = (dateStr?: string) => {
    if (!dateStr) return 'text-gray-500'
    const days = Math.ceil((new Date(dateStr).getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    if (days < 0) return 'text-red-600 font-semibold'
    if (days <= 2) return 'text-orange-600 font-medium'
    return 'text-gray-600'
  }

  // KPI Card component
  const KpiCard = ({ label, value, sub, icon, color }: {
    label: string; value: number | string; sub: string; icon: React.ReactNode; color: string
  }) => {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mein Tag</h1>
          <p className="text-gray-500 text-sm mt-0.5">Cockpit · {monatLabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            Letzte Aktualisierung: {format(now, 'HH:mm')}
          </span>
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

      {/* Three main sections per spec */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Section 1: Heute kritisch */}
        <div className="lg:col-span-1">
          <div className="card h-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-red-700 flex items-center gap-2">
                <AlertCircle size={18} />
                Heute kritisch
              </h2>
              <span className="badge bg-red-100 text-red-700">
                {meinTag?.kritisch.length ?? 0}
              </span>
            </div>

            {meinTagLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-20 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : meinTag?.kritisch.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 size={40} className="mx-auto text-green-500 mb-2" />
                <p className="text-sm text-gray-500">Keine kritischen Fälle</p>
              </div>
            ) : (
              <div className="space-y-3">
                {meinTag?.kritisch.slice(0, 5).map((item) => (
                  <KritischCard 
                    key={`${item.mandant_id}-${item.workflow_id}`} 
                    item={item} 
                    onReminder={() => navigate(`/mandanten/${item.mandant_id}?action=reminder`)}
                    onNavigate={() => navigate(`/workflows/${item.workflow_id}`)}
                    formatDate={formatDate}
                    getUrgencyColor={getUrgencyColor}
                  />
                ))}
                {meinTag && meinTag.kritisch.length > 5 && (
                  <button
                    onClick={() => navigate('/mandanten?filter=kritisch')}
                    className="w-full text-sm text-blue-600 hover:text-blue-800 flex items-center justify-center gap-1 py-2"
                  >
                    + {meinTag.kritisch.length - 5} weitere anzeigen
                    <ArrowRight size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Wartet auf Mandant */}
        <div className="lg:col-span-1">
          <div className="card h-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-purple-700 flex items-center gap-2">
                <Clock size={18} />
                Wartet auf Mandant
              </h2>
              <span className="badge bg-purple-100 text-purple-700">
                {meinTag?.wartet_auf_mandant.length ?? 0}
              </span>
            </div>

            {meinTagLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : meinTag?.wartet_auf_mandant.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 size={40} className="mx-auto text-green-500 mb-2" />
                <p className="text-sm text-gray-500">Keine offenen Rückfragen</p>
              </div>
            ) : (
              <div className="space-y-3">
                {meinTag?.wartet_auf_mandant.slice(0, 5).map((item) => (
                  <WartetCard
                    key={`${item.ticket_id}`}
                    item={item}
                    onAnswer={() => item.ticket_id && handleAnswerTicket(item.ticket_id)}
                    formatDate={formatDate}
                  />
                ))}
                {meinTag && meinTag.wartet_auf_mandant.length > 5 && (
                  <button
                    onClick={() => navigate('/tickets?filter=wartet')}
                    className="w-full text-sm text-blue-600 hover:text-blue-800 flex items-center justify-center gap-1 py-2"
                  >
                    + {meinTag.wartet_auf_mandant.length - 5} weitere anzeigen
                    <ArrowRight size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Section 3: Meine Arbeit */}
        <div className="lg:col-span-1">
          <div className="card h-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-blue-700 flex items-center gap-2">
                <CheckSquare size={18} />
                Meine Arbeit
              </h2>
              <span className="badge bg-blue-100 text-blue-700">
                {meinTag?.meine_arbeit.length ?? 0}
              </span>
            </div>

            {meinTagLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : meinTag?.meine_arbeit.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 size={40} className="mx-auto text-green-500 mb-2" />
                <p className="text-sm text-gray-500">Keine offenen Aufgaben</p>
              </div>
            ) : (
              <div className="space-y-3">
                {meinTag?.meine_arbeit.slice(0, 5).map((item) => (
                  <MeineArbeitCard
                    key={`${item.typ}-${item.id}`}
                    item={item}
                    onComplete={() => handleCompleteStep(item)}
                    formatDate={formatDate}
                    getUrgencyColor={getUrgencyColor}
                  />
                ))}
                {meinTag && meinTag.meine_arbeit.length > 5 && (
                  <button
                    onClick={() => navigate('/workflows?filter=meine')}
                    className="w-full text-sm text-blue-600 hover:text-blue-800 flex items-center justify-center gap-1 py-2"
                  >
                    + {meinTag.meine_arbeit.length - 5} weitere anzeigen
                    <ArrowRight size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components for each section ──────────────────────────────────────────────

function KritischCard({ 
  item, 
  onReminder, 
  onNavigate,
  formatDate,
  getUrgencyColor
}: { 
  item: KritischInfo
  onReminder: () => void
  onNavigate: () => void
  formatDate: (d?: string) => string
  getUrgencyColor: (d?: string) => string
}) {
  return (
    <div className="p-3 rounded-lg border border-red-200 bg-red-50/50 hover:bg-red-50 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Ampel status={item.ampelstatus} size="sm" />
            <span className="text-sm font-medium text-gray-900 truncate">
              {item.mandant_name}
            </span>
          </div>
          <div className="mt-1 text-xs text-gray-500">
            <span className="font-medium">{item.stichtag_typ || 'Fällig'}</span>
            <span className="ml-1">· {formatDate(item.naechster_stichtag)}</span>
          </div>
          {item.blocker && (
            <div className="mt-1 text-xs text-red-600 truncate">
              ⚠️ {item.blocker}
            </div>
          )}
        </div>
        <div className="flex flex-col gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onReminder(); }}
            className="p-1.5 rounded hover:bg-red-100 text-red-600"
            title="Reminder senden"
          >
            <Mail size={14} />
          </button>
        </div>
      </div>
      <button
        onClick={onNavigate}
        className="mt-2 w-full text-xs text-blue-600 hover:text-blue-800 flex items-center justify-center gap-1"
      >
        Zum Workflow <ArrowRight size={12} />
      </button>
    </div>
  )
}

function WartetCard({ 
  item, 
  onAnswer,
  formatDate 
}: { 
  item: WartetAufMandantInfo
  onAnswer: () => void
  formatDate: (d?: string) => string
}) {
  return (
    <div className="p-3 rounded-lg border border-purple-200 bg-purple-50/50 hover:bg-purple-50 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <MessageSquare size={14} className="text-purple-500" />
            <span className="text-sm font-medium text-gray-900 truncate">
              {item.mandant_name}
            </span>
          </div>
          {item.ticket_titel && (
            <div className="mt-1 text-xs text-gray-500 truncate">
              {item.ticket_titel}
            </div>
          )}
          {item.wartet_seit && (
            <div className="mt-1 text-xs text-purple-600">
              Wartet seit: {item.wartet_seit}
            </div>
          )}
        </div>
      </div>
      {item.ticket_id && (
        <button
          onClick={onAnswer}
          className="mt-2 w-full text-xs bg-purple-100 text-purple-700 py-1.5 rounded hover:bg-purple-200 flex items-center justify-center gap-1"
        >
          <Send size={12} /> Antworten
        </button>
      )}
    </div>
  )
}

function MeineArbeitCard({ 
  item, 
  onComplete,
  formatDate,
  getUrgencyColor
}: { 
  item: MeineArbeitItem
  onComplete: () => void
  formatDate: (d?: string) => string
  getUrgencyColor: (d?: string) => string
}) {
  const priorityColors = {
    kritisch: 'border-l-red-500 bg-red-50',
    hoch: 'border-l-orange-500 bg-orange-50',
    normal: 'border-l-blue-500 bg-blue-50',
  }
  
  const priorityBadge = {
    kritisch: 'bg-red-100 text-red-700',
    hoch: 'bg-orange-100 text-orange-700',
    normal: 'bg-blue-100 text-blue-700',
  }

  return (
    <div className={`p-3 rounded-lg border border-l-4 ${priorityColors[item.prioritaet || 'normal']} hover:shadow-sm transition-colors`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {item.typ === 'workflow_schritt' ? (
              <CheckSquare size={14} className="text-blue-500" />
            ) : (
              <FileCheck size={14} className="text-green-500" />
            )}
            <span className="text-sm font-medium text-gray-900 truncate">
              {item.titel}
            </span>
          </div>
          <div className="mt-1 text-xs text-gray-500 truncate">
            {item.mandant_name}
            {item.monat && item.jahr && ` · ${item.monat}/${item.jahr}`}
          </div>
          <div className="mt-1 flex items-center gap-2">
            {item.prioritaet && (
              <span className={`text-xs px-1.5 py-0.5 rounded ${priorityBadge[item.prioritaet]}`}>
                {item.prioritaet === 'kritisch' ? '🔴' : item.prioritaet === 'hoch' ? '🟠' : ''} {item.prioritaet}
              </span>
            )}
            {item.faellig_datum && (
              <span className={`text-xs ${getUrgencyColor(item.faellig_datum)}`}>
                ⏰ {formatDate(item.faellig_datum)}
              </span>
            )}
            {item.punkte !== undefined && (
              <span className="text-xs text-gray-400">
                {item.punkte} Pkt
              </span>
            )}
          </div>
        </div>
      </div>
      <button
        onClick={onComplete}
        className="mt-2 w-full text-xs bg-green-100 text-green-700 py-1.5 rounded hover:bg-green-200 flex items-center justify-center gap-1"
      >
        <CheckCircle2 size={12} /> Erledigen
      </button>
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
