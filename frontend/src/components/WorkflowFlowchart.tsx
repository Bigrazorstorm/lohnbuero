import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { Check, Clock, AlertCircle, Lock, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { WorkflowInstanz, ChecklistItemStatus } from '../types'

// ─────────────────────────────────────────
// Kernel process step definitions (same order as WorkflowDetail list)
// ─────────────────────────────────────────
const PROCESS_STEPS = [
  { key: 'unterlagen_eingegangen_am', vonKey: 'unterlagen_eingegangen_von', faelligKey: 'unterlagen_faellig', label: 'Unterlagen eingegangen' },
  { key: 'probe_abrechnung_am', vonKey: 'probe_abrechnung_von', faelligKey: 'probe_abrechnung_faellig', label: 'Probeabrechnung' },
  { key: 'probe_geprueft_am', vonKey: 'probe_geprueft_von', faelligKey: 'probe_geprueft_faellig', label: 'Probe geprüft (4-Augen)' },
  { key: 'mandant_freigabe_am', vonKey: 'mandant_freigabe_von', faelligKey: 'mandant_freigabe_faellig', label: 'Mandantenfreigabe' },
  { key: 'endabrechnung_am', vonKey: 'endabrechnung_von', faelligKey: 'endabrechnung_faellig', label: 'Endabrechnung' },
  { key: 'versand_am', vonKey: 'versand_von', faelligKey: 'versand_faellig', label: 'Lohnzettel versandt' },
  { key: 'abgeschlossen_am', vonKey: 'abgeschlossen_von', faelligKey: 'abgeschlossen_faellig', label: 'Monatsabschluss' },
] as const

// ─────────────────────────────────────────
// Arrow connector between flow nodes
// ─────────────────────────────────────────
function FlowArrow() {
  return (
    <div className="flex-shrink-0 flex items-center justify-center w-8 text-gray-300">
      <svg width="28" height="20" viewBox="0 0 28 20" fill="none">
        <line x1="0" y1="10" x2="20" y2="10" stroke="#CBD5E1" strokeWidth="2" />
        <polygon points="16,4 28,10 16,16" fill="#CBD5E1" />
      </svg>
    </div>
  )
}

// ─────────────────────────────────────────
// Individual flow node card
// ─────────────────────────────────────────
interface FlowNodeProps {
  index: number
  label: string
  isDone: boolean
  isOverdue: boolean
  isBlocked: boolean
  dateLabel?: string
  byLabel?: string
  badge?: string
  badgeColor?: string
  isOptional?: boolean
  disabled: boolean
  onClick: () => void
}

function FlowNode({
  index,
  label,
  isDone,
  isOverdue,
  isBlocked,
  dateLabel,
  byLabel,
  badge,
  badgeColor = 'bg-gray-100 text-gray-600',
  isOptional,
  disabled,
  onClick,
}: FlowNodeProps) {
  const [expanded, setExpanded] = useState(false)

  const borderColor = isDone
    ? 'border-green-400'
    : isBlocked
    ? 'border-red-400'
    : isOverdue
    ? 'border-red-300'
    : 'border-amber-300'

  const bgColor = isDone
    ? 'bg-green-50'
    : isBlocked
    ? 'bg-red-50'
    : isOverdue
    ? 'bg-red-50'
    : 'bg-white'

  const statusIcon = isDone ? (
    <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
      <Check size={13} className="text-white" />
    </div>
  ) : isBlocked ? (
    <div className="w-6 h-6 rounded-full bg-red-400 flex items-center justify-center flex-shrink-0">
      <Lock size={12} className="text-white" />
    </div>
  ) : isOverdue ? (
    <div className="w-6 h-6 rounded-full bg-red-300 flex items-center justify-center flex-shrink-0">
      <AlertCircle size={12} className="text-white" />
    </div>
  ) : (
    <div className="w-6 h-6 rounded-full border-2 border-amber-300 flex-shrink-0" />
  )

  return (
    <div
      className={`flex-shrink-0 w-44 rounded-xl border-2 shadow-sm transition-all ${borderColor} ${bgColor}`}
    >
      {/* Card header: click to toggle done */}
      <button
        disabled={disabled}
        onClick={onClick}
        className={`w-full text-left px-3 pt-3 pb-2 flex items-start gap-2 ${disabled ? 'cursor-default' : 'hover:brightness-95'}`}
        title={disabled ? '' : isDone ? 'Als offen markieren' : 'Als erledigt markieren'}
      >
        {statusIcon}
        <div className="flex-1 min-w-0">
          <div className="text-xs text-gray-400 font-medium mb-0.5">Schritt {index + 1}</div>
          <div className={`text-sm font-semibold leading-tight ${isDone ? 'text-gray-500' : 'text-gray-800'}`}>
            {label}
          </div>
        </div>
      </button>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-3 pb-2 text-xs text-gray-400 hover:text-gray-600"
      >
        <div className="flex items-center gap-1 flex-wrap">
          {badge && (
            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${badgeColor}`}>{badge}</span>
          )}
          {isOptional && (
            <span className="px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-500">Optional</span>
          )}
        </div>
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 border-t border-gray-100 pt-2 space-y-1">
          {isDone && dateLabel && (
            <div className="flex items-center gap-1 text-xs text-green-600">
              <Check size={10} />
              <span>{dateLabel}</span>
            </div>
          )}
          {isDone && byLabel && (
            <div className="text-xs text-gray-500">von {byLabel}</div>
          )}
          {!isDone && dateLabel && (
            <div className={`flex items-center gap-1 text-xs ${isOverdue ? 'text-red-600 font-medium' : 'text-gray-400'}`}>
              <Clock size={10} />
              <span>Fällig: {dateLabel}</span>
            </div>
          )}
          {isBlocked && (
            <div className="text-xs text-red-600 flex items-center gap-1">
              <Lock size={10} />
              <span>Schritt ist blockiert</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────
// FlowSection: a labeled row of flow nodes
// ─────────────────────────────────────────
interface FlowSectionProps {
  title: string
  badge?: string
  badgeColor?: string
  children: React.ReactNode
}

function FlowSection({ title, badge, badgeColor = 'bg-amber-100 text-amber-700', children }: FlowSectionProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-3 border-b border-gray-100 bg-gray-50">
        <h3 className="font-semibold text-gray-800 text-sm">{title}</h3>
        {badge && (
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeColor}`}>{badge}</span>
        )}
      </div>
      <div className="overflow-x-auto">
        <div className="flex items-center gap-0 px-5 py-5 min-w-max">
          {children}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────
// Main Flowchart Component
// ─────────────────────────────────────────
interface WorkflowFlowchartProps {
  wf: WorkflowInstanz
  isMandant: boolean
  isPending: boolean
  onToggleProcessStep: (key: string, currentValue: string | undefined) => void
  onToggleItem: (itemId: number, currentStatus: ChecklistItemStatus) => void
}

export default function WorkflowFlowchart({
  wf,
  isMandant,
  isPending,
  onToggleProcessStep,
  onToggleItem,
}: WorkflowFlowchartProps) {
  const sortedItems = [...wf.items].sort((a, b) => a.position - b.position)

  // Check whether the template defines custom kernel process items
  const templateKernelItems = sortedItems.filter(item => item.ist_kernprozess)
  const useTemplateKernel = templateKernelItems.length > 0

  // ── Kernel Process Flow ──────────────────
  // If the template has items marked as kernel process, use those.
  // Otherwise fall back to the hardcoded PROCESS_STEPS (legacy behavior).
  const kernelNodes = useTemplateKernel
    ? templateKernelItems.map((item, idx) => {
        const isDone = item.status === 'erledigt'
        const isBlocked = !!(item.blockiert_von_item_ids && item.blockiert_von_item_ids.length > 0)
        const isOverdue = !!(item.faellig_datum && new Date(item.faellig_datum) < new Date() && !isDone)

        const dateLabel = isDone && item.erledigt_am
          ? format(new Date(item.erledigt_am), 'dd.MM.yyyy HH:mm', { locale: de })
          : item.faellig_datum
          ? format(new Date(item.faellig_datum), 'dd.MM.yyyy', { locale: de })
          : undefined

        return (
          <span key={item.id} className="flex items-center">
            <FlowNode
              index={idx}
              label={item.titel}
              isDone={isDone}
              isOverdue={isOverdue}
              isBlocked={isBlocked}
              dateLabel={dateLabel}
              byLabel={item.erledigt_von?.full_name}
              badge="Kernprozess"
              badgeColor="bg-amber-100 text-amber-700"
              isOptional={!item.ist_pflicht}
              disabled={isMandant || isPending}
              onClick={() => onToggleItem(item.id, item.status)}
            />
            {idx < templateKernelItems.length - 1 && <FlowArrow />}
          </span>
        )
      })
    : PROCESS_STEPS.map((step, idx) => {
        const value = wf[step.key as keyof WorkflowInstanz] as string | undefined
        const erledigtVon = wf[step.vonKey as keyof WorkflowInstanz] as { full_name: string } | undefined
        const faellig = wf[step.faelligKey as keyof WorkflowInstanz] as string | undefined
        const isDone = !!value
        const isOverdue = !!faellig && !isDone && new Date(faellig) < new Date()

        const dateLabel = isDone
          ? format(new Date(value!), 'dd.MM.yyyy HH:mm', { locale: de })
          : faellig
          ? format(new Date(faellig), 'dd.MM.yyyy', { locale: de })
          : undefined

        return (
          <span key={step.key} className="flex items-center">
            <FlowNode
              index={idx}
              label={step.label}
              isDone={isDone}
              isOverdue={isOverdue}
              isBlocked={false}
              dateLabel={dateLabel}
              byLabel={erledigtVon?.full_name}
              badge="Kernprozess"
              badgeColor="bg-amber-100 text-amber-700"
              disabled={isMandant || isPending}
              onClick={() => onToggleProcessStep(step.key, value)}
            />
            {idx < PROCESS_STEPS.length - 1 && <FlowArrow />}
          </span>
        )
      })

  // ── Non-kernel Checklist Items Flow ──────────────────
  const nonKernelItems = useTemplateKernel
    ? sortedItems.filter(item => !item.ist_kernprozess)
    : sortedItems

  const checklistNodes = nonKernelItems.map((item, idx) => {
    const isDone = item.status === 'erledigt'
    const isBlocked = !!(item.blockiert_von_item_ids && item.blockiert_von_item_ids.length > 0)
    const isOverdue = !!(item.faellig_datum && new Date(item.faellig_datum) < new Date() && !isDone)

    const dateLabel = isDone && item.erledigt_am
      ? format(new Date(item.erledigt_am), 'dd.MM.yyyy HH:mm', { locale: de })
      : item.faellig_datum
      ? format(new Date(item.faellig_datum), 'dd.MM.yyyy', { locale: de })
      : undefined

    const ebene = item.herkunft?.ebene
    const badge = ebene === 'branche' ? 'Branche' : ebene === 'mandant' ? 'Mandant' : ebene === 'global_event' ? 'Global' : 'Standard'
    const badgeColor = ebene === 'branche'
      ? 'bg-purple-100 text-purple-700'
      : ebene === 'mandant'
      ? 'bg-green-100 text-green-700'
      : ebene === 'global_event'
      ? 'bg-yellow-100 text-yellow-700'
      : 'bg-blue-100 text-blue-700'

    return (
      <span key={item.id} className="flex items-center">
        <FlowNode
          index={idx}
          label={item.titel}
          isDone={isDone}
          isOverdue={isOverdue}
          isBlocked={isBlocked}
          dateLabel={dateLabel}
          byLabel={item.erledigt_von?.full_name}
          badge={badge}
          badgeColor={badgeColor}
          isOptional={!item.ist_pflicht}
          disabled={isMandant || isPending}
          onClick={() => onToggleItem(item.id, item.status)}
        />
        {idx < nonKernelItems.length - 1 && <FlowArrow />}
      </span>
    )
  })

  // Count completed kernel process steps
  const kernelDoneCount = useTemplateKernel
    ? templateKernelItems.filter(i => i.status === 'erledigt').length
    : PROCESS_STEPS.filter(s => wf[s.key as keyof WorkflowInstanz]).length
  const kernelTotal = useTemplateKernel ? templateKernelItems.length : PROCESS_STEPS.length

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 px-1">
        <span className="font-medium text-gray-600">Legende:</span>
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
            <Check size={9} className="text-white" />
          </span>
          Erledigt
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full border-2 border-amber-300" />
          Ausstehend
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-red-300 flex items-center justify-center">
            <AlertCircle size={9} className="text-white" />
          </span>
          Überfällig
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-red-400 flex items-center justify-center">
            <Lock size={9} className="text-white" />
          </span>
          Blockiert
        </span>
        {!isMandant && (
          <span className="ml-auto text-gray-400 italic">Auf Schritt klicken zum Abhaken</span>
        )}
      </div>

      {/* Kernel Process Flow */}
      <FlowSection
        title="Kernprozess-Ablauf"
        badge={`${kernelDoneCount} / ${kernelTotal} erledigt`}
        badgeColor="bg-amber-100 text-amber-700"
      >
        {kernelNodes}
      </FlowSection>

      {/* Non-kernel Checklist Item Flow */}
      {nonKernelItems.length > 0 && (
        <FlowSection
          title="Weitere Workflow-Schritte"
          badge={`${nonKernelItems.filter(i => i.status === 'erledigt').length} / ${nonKernelItems.length} erledigt`}
          badgeColor="bg-blue-100 text-blue-700"
        >
          {checklistNodes}
        </FlowSection>
      )}

      {sortedItems.length === 0 && (
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 text-center text-gray-400 text-sm">
          Keine zusätzlichen Workflow-Schritte für diesen Monat
        </div>
      )}
    </div>
  )
}
