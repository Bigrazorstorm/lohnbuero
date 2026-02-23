import React, { useState } from 'react'
import { WorkflowPhase, WorkflowItem, ChecklistItemStatus, WorkflowItemStatus } from '../types'

interface PhaseAccordionProps {
  phase: WorkflowPhase
  items: WorkflowItem[]
  onItemStatusChange: (itemId: number, newStatus: ChecklistItemStatus) => void
  onItemClick?: (item: WorkflowItem) => void
}

export default function PhaseAccordion({
  phase,
  items,
  onItemStatusChange,
  onItemClick,
}: PhaseAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  // Calculate phase statistics
  const total = items.length
  const completed = items.filter((i) => i.status === 'erledigt').length
  const blocked = items.filter((i) => i.status === 'blockiert' || (i.blockiert_von_item_ids && i.blockiert_von_item_ids.length > 0)).length
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0

  const statusColor = (status: ChecklistItemStatus | WorkflowItemStatus): string => {
    switch (status) {
      case 'erledigt':
        return 'bg-green-50 border-green-200'
      case 'blockiert':
        return 'bg-red-50 border-red-200'
      case 'in_bearbeitung':
        return 'bg-blue-50 border-blue-200'
      case 'uebersprungen':
        return 'bg-gray-50 border-gray-200'
      default:
        return 'bg-yellow-50 border-yellow-200'
    }
  }

  const statusIcon = (status: ChecklistItemStatus | WorkflowItemStatus | undefined): string => {
    switch (status) {
      case 'erledigt':
        return '✅'
      case 'blockiert':
        return '🚫'
      case 'in_bearbeitung':
        return '⏱️'
      case 'uebersprungen':
        return '⏭️'
      default:
        return '⭕'
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4">
      {/* Phase Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 transition-colors flex items-center justify-between border-b border-gray-200"
      >
        <div className="flex items-center gap-3 flex-1">
          <span className="text-2xl">{phase.icon}</span>
          <div className="text-left">
            <h3 className="font-bold text-lg">{phase.name}</h3>
            <div className="text-sm text-gray-600">
              {completed}/{total} erledigt • {blocked} blockiert
              {phase.standard_frist_tag && (
                <span className="ml-2">📅 {phase.standard_frist_tag}. des Monats</span>
              )}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="flex items-center gap-3">
          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                progress === 100 ? 'bg-green-500' : progress > 50 ? 'bg-blue-500' : 'bg-yellow-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-gray-700 w-8 text-right">{progress}%</span>
          <span className="text-xl ml-2">{isExpanded ? '▼' : '▶'}</span>
        </div>
      </button>

      {/* Phase Items */}
      {isExpanded && (
        <div className="divide-y divide-gray-200">
          {items.length === 0 ? (
            <div className="p-4 text-center text-gray-500">Keine Items in dieser Phase</div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className={`p-4 border-l-4 transition-colors ${statusColor(item.status)} ${
                  item.status === 'blockiert' ? 'border-l-red-500' : 'border-l-blue-500'
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Checkbox/Status */}
                  <button
                    onClick={() => {
                      const newStatus: ChecklistItemStatus =
                        item.status === 'erledigt' ? 'offen' : 'erledigt'
                      onItemStatusChange(item.id, newStatus)
                    }}
                    className="mt-1 flex-shrink-0 text-2xl hover:scale-110 transition-transform"
                    title={item.status}
                  >
                    {statusIcon(item.status)}
                  </button>

                  {/* Item Details */}
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => onItemClick?.(item)}
                  >
                    <div className={item.status === 'erledigt' ? 'line-through text-gray-500' : ''}>
                      <p className="font-semibold">{item.titel}</p>
                      {item.beschreibung && (
                        <p className="text-sm text-gray-600 mt-1">{item.beschreibung}</p>
                      )}
                    </div>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-600">
                      {item.ist_pflicht && <span className="bg-red-100 text-red-800 px-2 py-1 rounded">Pflicht</span>}
                      {item.erfordert_dokument && (
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">📎 Dokument</span>
                      )}
                      {item.erfordert_pruefung && (
                        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">👥 Prüfung</span>
                      )}
                      {item.faellig_datum && (
                        <span
                          className={
                            new Date(item.faellig_datum) < new Date()
                              ? 'bg-red-100 text-red-800 px-2 py-1 rounded'
                              : 'bg-yellow-100 text-yellow-800 px-2 py-1 rounded'
                          }
                        >
                          📅 {new Date(item.faellig_datum).toLocaleDateString('de-DE')}
                        </span>
                      )}
                    </div>

                    {/* Blockage Info */}
                    {item.blockiert_von_item_ids && item.blockiert_von_item_ids.length > 0 && (
                      <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-sm text-red-800">
                        <strong className="block">🔒 Blockiert durch:</strong>
                        <span>{item.blockiert_grund || `${item.blockiert_von_item_ids.length} Items`}</span>
                      </div>
                    )}

                    {/* Notiz */}
                    {item.notiz && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-sm italic">{item.notiz}</div>
                    )}
                  </div>

                  {/* Punkte */}
                  {item.punkte && item.punkte > 0 && (
                    <div className="flex-shrink-0 text-right">
                      <div className="font-bold text-lg text-amber-600">{item.punkte}</div>
                      <div className="text-xs text-gray-600">Punkte</div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
