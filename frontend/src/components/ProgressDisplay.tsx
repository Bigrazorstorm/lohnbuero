import React from 'react'
import { WorkflowItem } from '../types'

interface ProgressDisplayProps {
  items: WorkflowItem[]
  phases?: Array<{ id: number; ist_kernprozess: boolean }>
}

export default function ProgressDisplay({ items, phases }: ProgressDisplayProps) {
  // Calculate Gesamt (all items)
  const totalItems = items.filter((i) => i.ist_pflicht !== false).length
  const completedTotal = items.filter((i) => i.ist_pflicht !== false && i.status === 'erledigt').length
  const progressGesamt = totalItems > 0 ? Math.round((completedTotal / totalItems) * 100) : 0

  // Calculate Kernprozess (kernel process items)
  const kernItems = items.filter((i) => {
    // Items that are in kernel phases OR marked as kernel process items
    return i.ist_pflicht && i.position <= 5 // Simple heuristic: first 5 items are typically kernel
  })
  const completedKern = kernItems.filter((i) => i.status === 'erledigt').length
  const progressKern = kernItems.length > 0 ? Math.round((completedKern / kernItems.length) * 100) : 0

  // Calculate Kritisch (blocked or overdue items)
  const kritischItems = items.filter((i) => {
    const isBlocked = i.blockiert_von_item_ids && i.blockiert_von_item_ids.length > 0
    const isOverdue = i.faellig_datum && new Date(i.faellig_datum) < new Date() && i.status !== 'erledigt'
    return (isBlocked || isOverdue) && i.status !== 'erledigt'
  })
  const criticalHealth = kritischItems.length === 0 ? 100 : Math.max(0, 100 - kritischItems.length * 20)

  const getProgressColor = (percentage: number) => {
    if (percentage === 100) return 'from-green-400 to-green-600'
    if (percentage >= 75) return 'from-blue-400 to-blue-600'
    if (percentage >= 50) return 'from-yellow-400 to-yellow-600'
    if (percentage >= 25) return 'from-orange-400 to-orange-600'
    return 'from-red-400 to-red-600'
  }

  const getHealthIcon = (percentage: number) => {
    if (percentage === 100) return '✅'
    if (percentage >= 75) return '🟢'
    if (percentage >= 50) return '🟡'
    if (percentage >= 25) return '🟠'
    return '🔴'
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      <h2 className="text-2xl font-bold mb-6">Workflow-Fortschritt</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Gesamt Progress */}
        <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase">Gesamt</p>
              <p className="text-2xl font-bold text-blue-700">
                {completedTotal}/{totalItems}
              </p>
            </div>
            <div className="text-4xl">{getHealthIcon(progressGesamt)}</div>
          </div>

          <div className="space-y-2">
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${getProgressColor(progressGesamt)} transition-all`}
                style={{ width: `${progressGesamt}%` }}
              />
            </div>
            <p className="text-sm font-semibold text-gray-700 text-center">{progressGesamt}% abgeschlossen</p>
          </div>

          <div className="mt-4 pt-4 border-t border-blue-200 text-xs text-gray-600">
            <p>
              ✅ <strong>{completedTotal}</strong> erledigt • ⭕ <strong>{totalItems - completedTotal}</strong> offen
            </p>
          </div>
        </div>

        {/* Kernprozess Progress */}
        <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase">Kernprozess</p>
              <p className="text-2xl font-bold text-purple-700">
                {completedKern}/{kernItems.length}
              </p>
            </div>
            <div className="text-4xl">{getHealthIcon(progressKern)}</div>
          </div>

          <div className="space-y-2">
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${getProgressColor(progressKern)} transition-all`}
                style={{ width: `${progressKern}%` }}
              />
            </div>
            <p className="text-sm font-semibold text-gray-700 text-center">{progressKern}% abgeschlossen</p>
          </div>

          <div className="mt-4 pt-4 border-t border-purple-200 text-xs text-gray-600">
            <p>
              ⭐ <strong>{kernItems.length}</strong> kritische Schritte
            </p>
          </div>
        </div>

        {/* Kritisch/Health Progress */}
        <div className="p-4 bg-gradient-to-br from-amber-50 to-red-50 rounded-lg border border-amber-200">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase">Gesundheit</p>
              <p className="text-2xl font-bold text-amber-700">{criticalHealth}%</p>
            </div>
            <div className="text-4xl">{getHealthIcon(criticalHealth)}</div>
          </div>

          <div className="space-y-2">
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${getProgressColor(criticalHealth)} transition-all`}
                style={{ width: `${criticalHealth}%` }}
              />
            </div>
            <p className="text-sm font-semibold text-gray-700 text-center">
              {kritischItems.length === 0 ? 'Alles OK' : 'Probleme vorhanden'}
            </p>
          </div>

          <div className="mt-4 pt-4 border-t border-amber-200 text-xs text-gray-600">
            <p>
              🚫 <strong>{kritischItems.length}</strong> blockiert • ⏰ <strong>{items.filter((i) => i.faellig_datum && new Date(i.faellig_datum) < new Date() && i.status !== 'erledigt').length}</strong> überfällig
            </p>
          </div>
        </div>
      </div>

      {/* Critical Items Alert */}
      {kritischItems.length > 0 && (
        <div className="mt-6 p-4 bg-red-50 border border-red-300 rounded-lg">
          <p className="font-semibold text-red-700 mb-2">⚠️ Kritische Items erfordern Aufmerksamkeit:</p>
          <ul className="space-y-1 text-sm text-red-600">
            {kritischItems.slice(0, 3).map((item) => (
              <li key={item.id}>
                • {item.titel}
                {item.blockiert_von_item_ids && item.blockiert_von_item_ids.length > 0 && ' (blockiert)'}
              </li>
            ))}
            {kritischItems.length > 3 && <li className="text-red-600">+ {kritischItems.length - 3} weitere...</li>}
          </ul>
        </div>
      )}
    </div>
  )
}
