import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { workflowsApi } from '../api/client'
import type { WorkflowInstanz, ChecklistItemStatus, WorkflowPhase, WorkflowItem, BlockedItemSummary } from '../types'
import Ampel from '../components/Ampel'
import { WorkflowStatusBadge } from '../components/StatusBadge'
import PhaseAccordion from '../components/PhaseAccordion'
import ProgressDisplay from '../components/ProgressDisplay'
import { useAuthStore } from '../store/auth'

/**
 * WorkflowDetail - Phase-based workflow visualization
 * NEW (v2.1): Uses accordion-based phase structure with dependency tracking
 */
export default function WorkflowDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuthStore()

  const [selectedItem, setSelectedItem] = useState<WorkflowItem | null>(null)

  const { data: wf, isLoading } = useQuery<WorkflowInstanz>({
    queryKey: ['workflow', id],
    queryFn: () => workflowsApi.get(Number(id)).then((r) => r.data),
    refetchInterval: 5000,
  })

  const { data: blockedItems } = useQuery({
    queryKey: ['workflow-blocked', id],
    queryFn: () => workflowsApi.listBlockedItems(Number(id)).then((r) => r.data),
    enabled: !!id,
    refetchInterval: 10000,
  })

  const itemMutation = useMutation({
    mutationFn: ({ itemId, status, notiz }: { itemId: number; status?: ChecklistItemStatus; notiz?: string }) =>
      workflowsApi.updateItem(Number(id), itemId, { status, notiz }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow', id] })
      qc.invalidateQueries({ queryKey: ['workflow-blocked', id] })
      toast.success('Item aktualisiert')
    },
    onError: (err) => {
      toast.error('Fehler beim Aktualisieren')
      console.error(err)
    },
  })

  if (isLoading) return <div className="text-center py-12 text-gray-400">Lädt…</div>
  if (!wf) return <div className="text-center py-12 text-red-500">Workflow nicht gefunden</div>

  const monatLabel = format(new Date(wf.jahr, wf.monat - 1, 1), 'MMMM yyyy', { locale: de })
  const isMandant = user?.role === 'mandant'

  const handleItemStatusChange = (itemId: number, newStatus: ChecklistItemStatus) => {
    if (isMandant) {
      toast.error('Sie haben keine Berechtigung, Items zu aktualisieren')
      return
    }

    itemMutation.mutate({ itemId, status: newStatus })
  }

  // Group items by phase
  const itemsByPhase: Record<number, WorkflowItem[]> = {}
  const phases: WorkflowPhase[] = []

  if (wf.vorlage?.phasen) {
    wf.vorlage.phasen.forEach((phase: WorkflowPhase) => {
      phases.push(phase)
      itemsByPhase[phase.id] = wf.items.filter((item) => item.phase_id === phase.id)
    })
  } else {
    // Fallback: group items without explicit phases
    itemsByPhase[0] = wf.items
    phases.push({
      id: 0,
      vorlage_id: wf.vorlage_id || 0,
      position: 1,
      name: 'Allgemeine Schritte',
      icon: '📋',
      ist_kernprozess: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 sticky top-0 z-10 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            <button
              onClick={() => navigate(-1)}
              className="flex-shrink-0 p-2 hover:bg-gray-100 rounded transition-colors"
            >
              <ArrowLeft size={20} />
            </button>

            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold">{wf.mandant?.name}</h1>
                <WorkflowStatusBadge status={wf.status} />
              </div>
              <p className="text-gray-600">
                {monatLabel} • ID: {wf.id}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Ampel status={wf.ampelstatus} size="lg" />
          </div>
        </div>
      </div>

      {/* Critical Alerts */}
      {blockedItems && blockedItems.length > 0 && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0 mt-1" size={20} />
            <div>
              <h3 className="font-bold text-red-700 mb-2">⚠️ {blockedItems.length} blockierte Items</h3>
              <ul className="space-y-1 text-sm text-red-600">
                {blockedItems.slice(0, 3).map((item: BlockedItemSummary) => (
                  <li key={item.id}>• {item.titel}</li>
                ))}
                {blockedItems.length > 3 && <li className="text-red-600">+ {blockedItems.length - 3} weitere…</li>}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Progress Display - 3-tier */}
      <ProgressDisplay items={wf.items} phases={wf.vorlage?.phasen || []} />

      {/* Phase Accordions */}
      <div>
        <h2 className="text-xl font-bold mb-4 px-6">Workflow-Schritte</h2>
        {phases.map((phase: WorkflowPhase) => (
          <PhaseAccordion
            key={phase.id}
            phase={phase}
            items={itemsByPhase[phase.id] || []}
            onItemStatusChange={handleItemStatusChange}
            onItemClick={setSelectedItem}
          />
        ))}
      </div>

      {/* Selected Item Detail Panel */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-2xl font-bold">{selectedItem.titel}</h2>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {selectedItem.beschreibung && (
                <div>
                  <h3 className="font-semibold mb-2">Beschreibung</h3>
                  <p className="text-gray-700">{selectedItem.beschreibung}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="font-semibold">{selectedItem.status}</p>
                </div>
                {selectedItem.faellig_datum && (
                  <div>
                    <p className="text-sm text-gray-600">Fällig</p>
                    <p className="font-semibold">
                      {format(new Date(selectedItem.faellig_datum), 'dd. MMMM yyyy', { locale: de })}
                    </p>
                  </div>
                )}
                {selectedItem.erledigt_am && (
                  <div>
                    <p className="text-sm text-gray-600">Erledigt</p>
                    <p className="font-semibold">
                      {format(new Date(selectedItem.erledigt_am), 'dd. MMMM yyyy', { locale: de })}
                    </p>
                  </div>
                )}
                {selectedItem.punkte && (
                  <div>
                    <p className="text-sm text-gray-600">Punkte</p>
                    <p className="font-semibold">{selectedItem.punkte}</p>
                  </div>
                )}
              </div>

              {selectedItem.blockiert_grund && (
                <div className="p-3 bg-red-50 rounded border border-red-200">
                  <p className="text-sm text-red-700">
                    <strong>🔒 Blockiert:</strong> {selectedItem.blockiert_grund}
                  </p>
                </div>
              )}

              {selectedItem.notiz && (
                <div>
                  <h3 className="font-semibold mb-2">Notiz</h3>
                  <p className="text-gray-700 p-3 bg-gray-50 rounded">{selectedItem.notiz}</p>
                </div>
              )}

              {!isMandant && (
                <div className="pt-4 border-t space-y-2">
                  <button
                    onClick={() => {
                      const newStatus: ChecklistItemStatus =
                        selectedItem.status === 'erledigt' ? 'offen' : 'erledigt'
                      handleItemStatusChange(selectedItem.id, newStatus)
                      setSelectedItem(null)
                    }}
                    className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-semibold"
                  >
                    {selectedItem.status === 'erledigt' ? 'Zurücksetzen' : 'Abschließen'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Workflow Metadata Footer */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-bold mb-3">Workflow-Informationen</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Status</p>
            <p className="font-semibold">{wf.status}</p>
          </div>
          {wf.sachbearbeiter && (
            <div>
              <p className="text-gray-600">Sachbearbeiter</p>
              <p className="font-semibold">{wf.sachbearbeiter.full_name}</p>
            </div>
          )}
          {wf.sla_deadline && (
            <div>
              <p className="text-gray-600">SLA Deadline</p>
              <p className="font-semibold">
                {format(new Date(wf.sla_deadline), 'dd.MM.yyyy', { locale: de })}
              </p>
            </div>
          )}
          <div>
            <p className="text-gray-600">Punkte</p>
            <p className="font-semibold">{wf.punkte || 0}</p>
          </div>
        </div>

        {wf.notizen && (
          <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
            <p className="text-xs text-gray-600 mb-1">Notizen</p>
            <p className="text-sm">{wf.notizen}</p>
          </div>
        )}
      </div>
    </div>
  )
}
