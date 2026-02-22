import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Check, Clock, AlertCircle, Lock } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { workflowsApi } from '../api/client'
import type { WorkflowInstanz, ChecklistItemStatus, WorkflowStatus } from '../types'
import Ampel from '../components/Ampel'
import { WorkflowStatusBadge, ChecklistStatusBadge } from '../components/StatusBadge'
import { useAuthStore } from '../store/auth'

const PROCESS_STEPS = [
  { key: 'unterlagen_eingegangen_am', label: 'Unterlagen eingegangen' },
  { key: 'probe_abrechnung_am', label: 'Probeabrechnung erstellt' },
  { key: 'probe_geprueft_am', label: 'Probeabrechnung geprüft (4-Augen)' },
  { key: 'mandant_freigabe_am', label: 'Mandantenfreigabe erteilt' },
  { key: 'endabrechnung_am', label: 'Endabrechnung durchgeführt' },
  { key: 'versand_am', label: 'Lohnzettel versandt' },
  { key: 'abgeschlossen_am', label: 'Monatsabschluss dokumentiert' },
] as const

export default function WorkflowDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [reOpenReason, setReOpenReason] = useState('')
  const [showReOpen, setShowReOpen] = useState(false)
  const [closingErrors, setClosingErrors] = useState<string[]>([])

  const { data: wf, isLoading } = useQuery<WorkflowInstanz>({
    queryKey: ['workflow', id],
    queryFn: () => workflowsApi.get(Number(id)).then((r) => (r as { data: WorkflowInstanz }).data),
  })

  const itemMutation = useMutation({
    mutationFn: ({ itemId, status, notiz }: { itemId: number; status?: ChecklistItemStatus; notiz?: string }) =>
      workflowsApi.updateItem(Number(id), itemId, { status, notiz }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflow', id] }),
    onError: () => toast.error('Fehler beim Aktualisieren'),
  })

  const workflowMutation = useMutation({
    mutationFn: (data: Partial<WorkflowInstanz> & { [key: string]: unknown }) =>
      workflowsApi.update(Number(id), data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow', id] })
      setClosingErrors([])
      setShowReOpen(false)
      toast.success('Gespeichert')
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: { fehler?: string[]; message?: string } | string } } }).response?.data?.detail
      if (detail && typeof detail === 'object' && 'fehler' in detail) {
        setClosingErrors(detail.fehler ?? [])
        toast.error(detail.message ?? 'Monatsabschluss nicht möglich')
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Fehler')
      }
    },
  })

  if (isLoading) return <div className="text-center py-12 text-gray-400">Laden…</div>
  if (!wf) return <div className="text-center py-12 text-red-500">Workflow nicht gefunden</div>

  const monatLabel = format(new Date(wf.jahr, wf.monat - 1, 1), 'MMMM yyyy', { locale: de })
  const isMandant = user?.role === 'mandant'

  const toggleItem = (itemId: number, currentStatus: ChecklistItemStatus) => {
    if (isMandant) return
    const newStatus: ChecklistItemStatus = currentStatus === 'erledigt' ? 'offen' : 'erledigt'
    itemMutation.mutate({ itemId, status: newStatus })
  }

  const markProcessStep = (key: string) => {
    const now = new Date().toISOString()
    workflowMutation.mutate({ [key]: now })
  }

  const completedCount = wf.items.filter(i => i.status === 'erledigt').length
  const totalRequired = wf.items.filter(i => i.ist_pflicht).length
  const progress = totalRequired > 0 ? Math.round((wf.items.filter(i => i.status === 'erledigt' && i.ist_pflicht).length / totalRequired) * 100) : 0

  // Calculate process steps completion
  const completedProcessSteps = PROCESS_STEPS.filter(step => wf[step.key as keyof WorkflowInstanz]).length

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="btn-secondary px-2 py-2">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900">
              {wf.mandant?.name ?? 'Mandant'} · {monatLabel}
            </h1>
            <Ampel status={wf.ampelstatus} size="lg" showLabel />
            <WorkflowStatusBadge status={wf.status} />
          </div>
          <p className="text-gray-400 text-sm mt-0.5">
            Sachbearbeiter: {wf.sachbearbeiter?.full_name ?? '–'}
            {wf.pruefer && ` · Prüfer: ${wf.pruefer.full_name}`}
          </p>
        </div>

        {/* Status change (staff only) */}
        {!isMandant && (
          <div className="flex gap-2">
            {wf.status !== 'abgeschlossen' && (
              <select
                className="input w-48 text-sm"
                value={wf.status}
                onChange={(e) => workflowMutation.mutate({ status: e.target.value as WorkflowStatus })}
              >
                <option value="offen">Offen</option>
                <option value="in_bearbeitung">In Bearbeitung</option>
                <option value="warte_freigabe">Warte Freigabe</option>
                <option value="eskaliert">Eskaliert</option>
                <option value="abgeschlossen">Abgeschlossen</option>
              </select>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Consolidated Checklist */}
        <div className="col-span-2 space-y-4">
          {/* Progress bar */}
          <div className="card py-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium text-gray-700">Fortschritt</span>
              <span className="text-gray-500">{completedProcessSteps + completedCount} / {PROCESS_STEPS.length + wf.items.length} Schritte ({Math.round(((completedProcessSteps + completedCount) / (PROCESS_STEPS.length + wf.items.length)) * 100)}%)</span>
            </div>
            <div className="w-full h-2.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${progress === 100 && completedProcessSteps === PROCESS_STEPS.length ? 'bg-green-500' : 'bg-blue-500'}`}
                style={{ width: `${Math.round(((completedProcessSteps + completedCount) / (PROCESS_STEPS.length + wf.items.length)) * 100)}%` }}
              />
            </div>
          </div>

          {/* Consolidated items list */}
          <div className="card space-y-2 py-4">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Prozessablauf & Checkliste</h2>

            <div className="space-y-2">
                {/* Kernprozess-Schritte */}
                {PROCESS_STEPS.map((step, idx) => {
                  const value = wf[step.key as keyof WorkflowInstanz] as string | undefined
                  const isDone = !!value

                  return (
                    <div
                      key={idx}
                      className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                        isDone
                          ? 'border-green-100 bg-green-50'
                          : 'border-amber-100 bg-amber-50'
                      }`}
                    >
                      {/* Checkmark */}
                      <div className={`mt-0.5 w-5 h-5 rounded flex-shrink-0 border-2 flex items-center justify-center ${
                        isDone ? 'bg-green-500 border-green-500' : 'border-amber-300'
                      }`}>
                        {isDone && <Check size={12} className="text-white" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm font-semibold ${isDone ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                            {step.label}
                          </span>
                          <span className="badge bg-amber-100 text-amber-700 text-xs font-medium">Kernprozess</span>
                        </div>
                        {isDone ? (
                          <p className="text-xs text-green-600 mt-1">
                            ✓ {format(new Date(value!), 'dd.MM.yyyy HH:mm', { locale: de })}
                          </p>
                        ) : !isMandant ? (
                          <button
                            className="text-xs text-blue-600 hover:underline mt-1"
                            onClick={() => markProcessStep(step.key)}
                            disabled={workflowMutation.isPending}
                          >
                            Jetzt markieren →
                          </button>
                        ) : null}
                      </div>
                    </div>
                  )
                })}

                {/* Separator if both sections exist */}
                {wf.items.length > 0 && (
                  <div className="my-2 border-t border-gray-200" />
                )}

                {/* Flexible checklist items */}
                {wf.items.length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-4">Keine zusätzlichen Checklisten-Einträge</p>
                ) : (
                  <>
                    {wf.items.map((item) => {
                      const isOverdue = item.faellig_datum && new Date(item.faellig_datum) < new Date() && item.status !== 'erledigt'
                      return (
                        <div
                          key={item.id}
                          className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                            item.status === 'erledigt'
                              ? 'border-green-100 bg-green-50'
                              : isOverdue
                              ? 'border-red-100 bg-red-50'
                              : 'border-gray-100 hover:border-gray-200'
                          }`}
                        >
                          {/* Checkbox */}
                          <button
                            disabled={isMandant || itemMutation.isPending}
                            onClick={() => toggleItem(item.id, item.status)}
                            className={`mt-0.5 w-5 h-5 rounded flex-shrink-0 border-2 flex items-center justify-center transition-colors ${
                              item.status === 'erledigt'
                                ? 'bg-green-500 border-green-500 text-white'
                                : 'border-gray-300 hover:border-green-400'
                            } ${isMandant ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                          >
                            {item.status === 'erledigt' && <Check size={12} />}
                          </button>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`text-sm font-medium ${item.status === 'erledigt' ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                                {item.titel}
                              </span>
                              {!item.ist_pflicht && <span className="badge bg-gray-100 text-gray-500 text-xs">Optional</span>}
                              {item.erfordert_pruefung && <span className="badge bg-purple-100 text-purple-600 text-xs">4-Augen</span>}
                              {item.erfordert_dokument && <span className="badge bg-blue-100 text-blue-600 text-xs">Dokument</span>}
                              {isOverdue && <AlertCircle size={14} className="text-red-500" />}
                            </div>
                            {item.beschreibung && (
                              <p className="text-xs text-gray-500 mt-0.5">{item.beschreibung}</p>
                            )}
                            <div className="flex items-center gap-3 mt-1">
                              {item.faellig_datum && (
                                <span className={`text-xs flex items-center gap-1 ${isOverdue ? 'text-red-600 font-medium' : 'text-gray-400'}`}>
                                  <Clock size={11} />
                                  Fällig: {format(new Date(item.faellig_datum), 'dd.MM.yyyy', { locale: de })}
                                </span>
                              )}
                              {item.erledigt_von && (
                                <span className="text-xs text-gray-400">
                                  Erledigt von {item.erledigt_von.full_name}
                                  {item.erledigt_am && ` · ${format(new Date(item.erledigt_am), 'dd.MM.', { locale: de })}`}
                                </span>
                              )}
                            </div>
                          </div>

                          <ChecklistStatusBadge status={item.status} />
                        </div>
                      )
                    })}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          {/* Process Summary Card */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Kernprozess-Status</h3>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Schritte abgeschlossen:</span>
              <span className="text-lg font-bold text-amber-600">{completedProcessSteps} / {PROCESS_STEPS.length}</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mt-2">
              <div
                className="h-full bg-amber-500 rounded-full transition-all"
                style={{ width: `${Math.round((completedProcessSteps / PROCESS_STEPS.length) * 100)}%` }}
              />
            </div>
          </div>

          {/* Notizen */}
          {!isMandant && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Notizen</h3>
              <textarea
                className="input h-32 resize-none text-sm"
                defaultValue={wf.notizen ?? ''}
                onBlur={(e) => {
                  if (e.target.value !== wf.notizen) {
                    workflowMutation.mutate({ notizen: e.target.value })
                  }
                }}
                placeholder="Interne Notizen…"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
