export type UserRole = 'admin' | 'teamleitung' | 'sachbearbeiter' | 'pruefer' | 'mandant'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface UserShort {
  id: number
  full_name: string
  email: string
  role: UserRole
}

export type MandantKategorie = 'A' | 'B' | 'C'
export type Abgabeweg = 'email' | 'post' | 'portal' | 'fax'

export interface Mandant {
  id: number
  nummer?: string
  name: string
  branche?: string
  ansprechpartner_name?: string
  ansprechpartner_email?: string
  ansprechpartner_telefon?: string
  lohnabschluss_tag: number
  abgabeweg: Abgabeweg
  kategorie: MandantKategorie
  service_level?: string
  mitarbeiteranzahl: number
  besonderheiten?: string
  sachbearbeiter_id?: number
  vertretung_id?: number
  portal_user_id?: number
  stundensatz?: number
  monatspauschale?: number
  ist_aktiv: boolean
  sachbearbeiter?: UserShort
  vertretung?: UserShort
  created_at: string
}

export type WorkflowStatus =
  | 'offen'
  | 'in_bearbeitung'
  | 'warte_freigabe'
  | 'abgeschlossen'
  | 'eskaliert'

export type Ampelstatus = 'gruen' | 'gelb' | 'rot'

export type ChecklistItemStatus = 'offen' | 'erledigt' | 'uebersprungen' | 'blockiert'

export interface WorkflowItem {
  id: number
  instanz_id: number
  position: number
  titel: string
  beschreibung?: string
  verantwortlich_rolle?: UserRole
  faellig_datum?: string
  ist_pflicht: boolean
  erfordert_dokument: boolean
  erfordert_pruefung: boolean
  status: ChecklistItemStatus
  erledigt_am?: string
  erledigt_von?: UserShort
  notiz?: string
}

export interface WorkflowInstanz {
  id: number
  mandant_id: number
  mandant?: { id: number; name: string; nummer?: string; kategorie: MandantKategorie; ist_aktiv: boolean }
  vorlage_id?: number
  monat: number
  jahr: number
  status: WorkflowStatus
  ampelstatus: Ampelstatus
  sachbearbeiter?: UserShort
  pruefer?: UserShort
  unterlagen_eingegangen_am?: string
  probe_abrechnung_am?: string
  probe_geprueft_am?: string
  mandant_freigabe_am?: string
  endabrechnung_am?: string
  versand_am?: string
  abgeschlossen_am?: string
  notizen?: string
  created_at: string
  items: WorkflowItem[]
}

export interface WorkflowInstanzShort {
  id: number
  mandant_id: number
  monat: number
  jahr: number
  status: WorkflowStatus
  ampelstatus: Ampelstatus
  mandant?: { id: number; name: string; nummer?: string; kategorie: MandantKategorie; ist_aktiv: boolean }
}

export type TicketStatus = 'offen' | 'in_bearbeitung' | 'beantwortet' | 'geschlossen'
export type TicketPrioritaet = 'niedrig' | 'normal' | 'hoch' | 'dringend'

export interface TicketKommentar {
  id: number
  ticket_id: number
  autor: UserShort
  inhalt: string
  created_at: string
}

export interface Ticket {
  id: number
  mandant_id: number
  mandant: { id: number; name: string; nummer?: string; kategorie: MandantKategorie; ist_aktiv: boolean }
  workflow_instanz_id?: number
  erstellt_von: UserShort
  zugewiesen_an?: UserShort
  titel: string
  beschreibung?: string
  status: TicketStatus
  prioritaet: TicketPrioritaet
  kategorie?: string
  faellig_bis?: string
  geschlossen_am?: string
  created_at: string
  updated_at: string
  kommentare: TicketKommentar[]
}

export interface DashboardStats {
  mandanten_gesamt: number
  mandanten_aktiv: number
  workflows_offen: number
  workflows_in_bearbeitung: number
  workflows_eskaliert: number
  tickets_offen: number
  tickets_dringend: number
  ampel_rot: number
  ampel_gelb: number
  ampel_gruen: number
}

export interface MandantAmpelInfo {
  mandant_id: number
  mandant_name: string
  mandant_kategorie: MandantKategorie
  workflow_id?: number
  monat?: number
  jahr?: number
  status?: WorkflowStatus
  ampelstatus: Ampelstatus
  sachbearbeiter?: UserShort
}

export interface WorkflowVorlageItem {
  id: number
  vorlage_id: number
  position: number
  titel: string
  beschreibung?: string
  verantwortlich_rolle?: UserRole
  faellig_offset_tage: number
  ist_pflicht: boolean
  erfordert_dokument: boolean
  erfordert_pruefung: boolean
}

export interface WorkflowVorlage {
  id: number
  name: string
  beschreibung?: string
  branche?: string
  ist_standard: boolean
  erstellt_von_id?: number
  created_at: string
  items: WorkflowVorlageItem[]
}
