import type { WorkflowStatus, TicketStatus, TicketPrioritaet, ChecklistItemStatus } from '../types'

const workflowColors: Record<WorkflowStatus, string> = {
  offen: 'bg-gray-100 text-gray-700',
  in_bearbeitung: 'bg-blue-100 text-blue-700',
  warte_freigabe: 'bg-purple-100 text-purple-700',
  abgeschlossen: 'bg-green-100 text-green-700',
  eskaliert: 'bg-red-100 text-red-700',
}

const workflowLabels: Record<WorkflowStatus, string> = {
  offen: 'Offen',
  in_bearbeitung: 'In Bearbeitung',
  warte_freigabe: 'Warte Freigabe',
  abgeschlossen: 'Abgeschlossen',
  eskaliert: 'Eskaliert',
}

const ticketColors: Record<TicketStatus, string> = {
  neu: 'bg-sky-100 text-sky-700',
  offen: 'bg-orange-100 text-orange-700',
  in_bearbeitung: 'bg-blue-100 text-blue-700',
  wartet_auf_mandant: 'bg-purple-100 text-purple-700',
  intern_in_klaerung: 'bg-indigo-100 text-indigo-700',
  beantwortet: 'bg-teal-100 text-teal-700',
  geloest: 'bg-green-100 text-green-700',
  geschlossen: 'bg-gray-100 text-gray-600',
}

const ticketLabels: Record<TicketStatus, string> = {
  neu: 'Neu',
  offen: 'Offen',
  in_bearbeitung: 'In Bearbeitung',
  wartet_auf_mandant: 'Wartet auf Mandant',
  intern_in_klaerung: 'Intern in Klärung',
  beantwortet: 'Beantwortet',
  geloest: 'Gelöst',
  geschlossen: 'Geschlossen',
}

const prioritaetColors: Record<TicketPrioritaet, string> = {
  niedrig: 'bg-gray-100 text-gray-600',
  normal: 'bg-blue-100 text-blue-700',
  hoch: 'bg-orange-100 text-orange-700',
  kritisch: 'bg-red-100 text-red-700',
  dringend: 'bg-red-100 text-red-700',
}

const prioritaetLabels: Record<TicketPrioritaet, string> = {
  niedrig: 'Niedrig',
  normal: 'Normal',
  hoch: 'Hoch',
  kritisch: 'Kritisch',
  dringend: 'Dringend',
}

const checklistColors: Record<ChecklistItemStatus, string> = {
  offen: 'bg-gray-100 text-gray-600',
  erledigt: 'bg-green-100 text-green-700',
  uebersprungen: 'bg-yellow-100 text-yellow-700',
  blockiert: 'bg-red-100 text-red-700',
}

const checklistLabels: Record<ChecklistItemStatus, string> = {
  offen: 'Offen',
  erledigt: 'Erledigt',
  uebersprungen: 'Übersprungen',
  blockiert: 'Blockiert',
}

export function WorkflowStatusBadge({ status }: { status: WorkflowStatus }) {
  return <span className={`badge ${workflowColors[status]}`}>{workflowLabels[status]}</span>
}

export function TicketStatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`badge ${ticketColors[status]}`}>{ticketLabels[status]}</span>
}

export function PrioritaetBadge({ prioritaet }: { prioritaet: TicketPrioritaet }) {
  return <span className={`badge ${prioritaetColors[prioritaet]}`}>{prioritaetLabels[prioritaet]}</span>
}

export function ChecklistStatusBadge({ status }: { status: ChecklistItemStatus }) {
  return <span className={`badge ${checklistColors[status]}`}>{checklistLabels[status]}</span>
}

export function KategorieBadge({ kategorie }: { kategorie: 'A' | 'B' | 'C' }) {
  const colors = { A: 'bg-purple-100 text-purple-700', B: 'bg-blue-100 text-blue-700', C: 'bg-gray-100 text-gray-600' }
  return <span className={`badge ${colors[kategorie]}`}>Klasse {kategorie}</span>
}
