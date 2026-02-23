export type UserRole = 'admin' | 'teamleitung' | 'sachbearbeiter' | 'pruefer' | 'mandant'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  workload_limit?: number
  current_workload?: number
  total_points_earned?: number
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

export interface Fristenprofil {
  id: number
  mandant_id: number
  name: string
  ist_aktiv: boolean
  regeln: FristenregelOut[]
  created_at: string
}

export interface FristenregelOut {
  id: number
  profil_id: number
  position: number
  fristart: string
  regeltyp: FristenRegeltyp
  regel_config: string
  bundesland?: string
  interne_vorfrist_tage: number
  ist_aktiv: boolean
}

export interface MandantKontakt {
  id: number
  mandant_id: number
  rolle: MandantKontaktRolle
  name: string
  email?: string
  telefon?: string
  ist_aktiv: boolean
  created_at: string
}

export interface MandantNotiz {
  id: number
  mandant_id: number
  version: number
  inhalt: string
  erstellt_von: UserShort
  created_at: string
}

export interface BlockerIndikator {
  typ: string
  beschreibung: string
}

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
  fristenprofil_id?: number
  ist_aktiv: boolean
  onboarding_abgeschlossen?: boolean
  workflow_konfiguration?: { optional_item_ids: number[] }
  sachbearbeiter?: UserShort
  vertretung?: UserShort
  fristenprofil?: Fristenprofil
  kontakte: MandantKontakt[]
  notizen: MandantNotiz[]
  branchen_liste: Branche[]
  aenderungen: MandantAenderung[]
  created_at: string
}

export interface MandantAenderung {
  id: number
  mandant_id: number
  aenderung_zum?: string
  status: string
  aenderungen: string
  erstellt_von: UserShort
  erstellt_am: string
  aktiviert_am?: string
  abgebrochen_am?: string
  abgebrochen_von?: UserShort
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
  blocker_von?: number // ID of blocking item
  punkte?: number
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
  unterlagen_eingegangen_von?: UserShort
  unterlagen_faellig?: string
  probe_abrechnung_am?: string
  probe_abrechnung_von?: UserShort
  probe_abrechnung_faellig?: string
  probe_geprueft_am?: string
  probe_geprueft_von?: UserShort
  probe_geprueft_faellig?: string
  mandant_freigabe_am?: string
  mandant_freigabe_von?: UserShort
  mandant_freigabe_faellig?: string
  endabrechnung_am?: string
  endabrechnung_von?: UserShort
  endabrechnung_faellig?: string
  versand_am?: string
  versand_von?: UserShort
  versand_faellig?: string
  abgeschlossen_am?: string
  abgeschlossen_von?: UserShort
  abgeschlossen_faellig?: string
  wiedereroeffnet_am?: string
  wiedereroeffnet_begruendung?: string
  notizen?: string
  punkte?: number
  blocker_indikatoren?: BlockerIndikator[]
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

// Extended ticket statuses per Nachtrag v1.5
export type TicketStatus =
  | 'neu'
  | 'offen'
  | 'in_bearbeitung'          // backward compat
  | 'wartet_auf_mandant'
  | 'wartet_intern'
  | 'intern_in_klaerung'
  | 'in_pruefung'
  | 'beantwortet'             // backward compat
  | 'geloest'
  | 'geschlossen'
  | 'abgebrochen'

export type TicketPrioritaet = 'niedrig' | 'normal' | 'hoch' | 'kritisch' | 'dringend'

export type EskalationStufe = 'reminder' | 'teamleitung' | 'leitung'

export type EmailLogStatus = 'gesendet' | 'zugestellt' | 'gebounced'

export type FristenRegeltyp = 'fixes_datum' | 'relativ_monatsende' | 'relativ_bankarbeitstage' | 'relativ_andere_frist' | 'ereignisbasiert'

export type SonderaufgabeStatus = 'offen' | 'in_bearbeitung' | 'abgeschlossen' | 'abgebrochen'

export type MandantKontaktRolle = 'ansprechpartner' | 'ticket_kommunikation' | 'upload_reminder'

export interface TicketKommentar {
  id: number
  ticket_id: number
  autor: UserShort
  inhalt: string
  ist_intern: boolean
  zitat_id?: number
  anhaenge: TicketAnhang[]
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
  eskalationsstufe?: EskalationStufe
  monat?: number
  jahr?: number
  geschlossen_am?: string
  created_at: string
  updated_at: string
  kommentare: TicketKommentar[]
  anhaenge: TicketAnhang[]
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

// ── Dashboard "Mein Tag" Sections ───────────────────────────
export interface KritischInfo {
  mandant_id: number
  mandant_name: string
  mandant_kategorie: MandantKategorie
  workflow_id: number
  monat: number
  jahr: number
  naechster_stichtag?: string
  stichtag_typ?: string
  ampelstatus: Ampelstatus
  sachbearbeiter?: UserShort
  blocker?: string
}

export interface WartetAufMandantInfo {
  mandant_id: number
  mandant_name: string
  workflow_id: number
  monat: number
  jahr: number
  ticket_id?: number
  ticket_titel?: string
  sachbearbeiter?: UserShort
  wartet_seit?: string
}

export interface MeineArbeitItem {
  typ: 'workflow_schritt' | 'sonderaufgabe'
  id: number
  titel: string
  mandant_id: number
  mandant_name: string
  monat?: number
  jahr?: number
  faellig_datum?: string
  punkte?: number
  prioritaet?: 'kritisch' | 'hoch' | 'normal'
}

export interface DashboardMeinTag {
  kritisch: KritischInfo[]
  wartet_auf_mandant: WartetAufMandantInfo[]
  meine_arbeit: MeineArbeitItem[]
}

export interface WorkflowVorlageItem {
  id: number
  vorlage_id: number
  position: number
  titel: string
  beschreibung?: string
  verantwortlich_rolle?: UserRole
  faellig_offset_tage: number
  ist_kernprozess: boolean
  ist_pflicht: boolean
  ist_optional_pro_mandant: boolean
  erfordert_dokument: boolean
  erfordert_pruefung: boolean
}

export interface WorkflowVorlage {
  id: number
  name: string
  beschreibung?: string
  branche?: string
  ist_standard: boolean
  ist_onboarding: boolean
  erstellt_von_id?: number
  created_at: string
  items: WorkflowVorlageItem[]
}

// ── Audit Log ──────────────────────────────────────────────
export interface AuditLog {
  id: number
  objekt_typ: string
  objekt_id?: number
  mandant_id?: number
  monat?: number
  jahr?: number
  aktionstyp: string
  alter_wert?: string
  neuer_wert?: string
  benutzer_id?: number
  benutzer?: UserShort
  benutzerrolle?: string
  zeitstempel: string
  ip_adresse?: string
  beschreibung?: string
}

// ── Email Templates ────────────────────────────────────────
export interface EmailTemplate {
  id: number
  name: string
  betreff: string
  html_inhalt: string
  text_inhalt?: string
  beschreibung?: string
  typ?: string
  ist_aktiv: boolean
  reihenfolge: number
  verzoegerung_tage: number
  created_at: string
  updated_at: string
}

export interface EmailLog {
  id: number
  template_id?: number
  mandant_id: number
  empfaenger: string
  betreff: string
  status: 'gesendet' | 'zugestellt' | 'gebounced'
  gesendet_am: string
  fehler?: string
}

export interface TicketKPIs {
  gesamt: number
  offen: number
  eskaliert: number
  kritisch_offen: number
  avg_antwortzeit_stunden?: number
}

// ── Branche (Admin Stammdaten) ────────────────────────────
export interface Branche {
  id: number
  name: string
  beschreibung?: string
  faktor: number
  soka_relevant: boolean
  tags?: string
  ist_archiviert: boolean
  created_at: string
  updated_at: string
}

// ── Ausgabeweg Config (Admin Stammdaten) ──────────────────
export interface AusgabewegConfig {
  id: number
  name: string
  beschreibung?: string
  ist_aktiv: boolean
  beeinflusst_workflow: boolean
  zusatz_workflow_schritt?: string
  created_at: string
  updated_at: string
}

// ── Ticket-Anhänge ────────────────────────────────────────
export interface TicketAnhang {
  id: number
  ticket_id: number
  kommentar_id?: number
  dateiname: string
  dateityp?: string
  dateigroesse?: number
  speicherort: string
  hash?: string
  hochgeladen_von?: UserShort
  ist_intern: boolean
  ist_geloescht: boolean
  created_at: string
}

// ── SMTP-Konfiguration ───────────────────────────────────
export interface SmtpKonfiguration {
  id: number
  name: string
  server: string
  port: number
  tls_ssl: string
  auth_user?: string
  absender_email: string
  reply_to?: string
  ist_aktiv: boolean
  created_at: string
  updated_at: string
}

// ── IMAP-Konfiguration ───────────────────────────────────
export interface ImapKonfiguration {
  id: number
  name: string
  server: string
  port: number
  tls_ssl: string
  auth_user?: string
  postfach: string
  ordner?: string
  polling_intervall_sekunden: number
  zuordnung_methode: string
  ist_aktiv: boolean
  created_at: string
  updated_at: string
}

// ── System-Defaults ──────────────────────────────────────
export interface SystemDefault {
  id: number
  bereich: string
  name: string
  konfiguration?: string
  ist_aktiv: boolean
  created_at: string
  updated_at: string
}

// ── Upload-Konfiguration ─────────────────────────────────
export interface UploadKonfiguration {
  id: number
  max_dateigroesse_mb: number
  erlaubte_dateitypen: string
  created_at: string
  updated_at: string
}
// ── v2.0: Multi-Tenancy ──────────────────────────────────
export interface Tenant {
  id: number
  name: string
  code: string
  beschreibung?: string
  logo_url?: string
  primaerfarbe?: string
  konfiguration?: string
  ist_aktiv: boolean
  created_at: string
  updated_at: string
}

export interface Abrechnungsfirma {
  id: number
  tenant_id: number
  name: string
  code: string
  beschreibung?: string
  strasse?: string
  plz?: string
  ort?: string
  land: string
  telefon?: string
  email?: string
  steuernummer?: string
  ustid?: string
  bank_name?: string
  iban?: string
  bic?: string
  workflow_konfiguration?: string
  ist_aktiv: boolean
  created_at: string
  updated_at: string
}

// ── Global Events ────────────────────────────────────────
export type GlobalEventTyp = 
  | 'jahreswechsel'
  | 'mindestlohn_erhoehung'
  | 'gesetzesaenderung'
  | 'sv_werte_aenderung'
  | 'steueraenderung'
  | 'kurzarbeit'
  | 'corona_massnahme'
  | 'sonstig'

export interface GlobalEventSchritt {
  id: number
  event_id: number
  position: number
  titel: string
  beschreibung?: string
  schritttyp: string
  einfuege_position: string
  referenz_schritt_id?: number
  faellig_offset_tage: number
  fristart_referenz?: string
  fristart_offset_tage: number
  ist_pflicht: boolean
  erfordert_dokument: boolean
  erfordert_pruefung: boolean
  verantwortlich_rolle?: UserRole
  standard_punkte: number
  anleitung?: string
  ist_aktiv: boolean
  created_at: string
}

export interface GlobalEvent {
  id: number
  tenant_id?: number
  typ: GlobalEventTyp
  name: string
  beschreibung?: string
  gueltig_von: string
  gueltig_bis?: string
  betroffene_monate?: string
  mandanten_filter?: string
  prioritaet: number
  ist_aktiv: boolean
  ist_abgeschlossen: boolean
  erstellt_von?: UserShort
  schritte: GlobalEventSchritt[]
  created_at: string
  updated_at: string
}

// ── Branchenspezifische Workflow-Schritte ────────────────
export interface BranchenWorkflowSchritt {
  id: number
  branche_id: number
  position: number
  titel: string
  beschreibung?: string
  schritttyp: string
  einfuege_position: string
  referenz_schritt_id?: number
  faellig_offset_tage: number
  fristart_referenz?: string
  fristart_offset_tage: number
  ist_pflicht: boolean
  ist_optional_pro_mandant: boolean
  erfordert_dokument: boolean
  erfordert_pruefung: boolean
  verantwortlich_rolle?: UserRole
  standard_punkte: number
  gueltig_von?: string
  gueltig_bis?: string
  ist_aktiv: boolean
  created_at: string
  updated_at: string
}

// ── Workflow-Item Herkunft ───────────────────────────────
export type WorkflowSchrittEbene = 'standard' | 'branche' | 'mandant' | 'global_event'

export interface WorkflowItemHerkunft {
  id: number
  workflow_item_id: number
  ebene: WorkflowSchrittEbene
  vorlage_item_id?: number
  branchen_schritt_id?: number
  mandant_schritt_id?: number
  global_event_schritt_id?: number
  created_at: string
}

export interface WorkflowItemMitHerkunft extends WorkflowItem {
  herkunft?: WorkflowItemHerkunft
  ebene?: WorkflowSchrittEbene
}

export interface WorkflowInstanzMitHerkunft extends WorkflowInstanz {
  items: WorkflowItemMitHerkunft[]
  global_events: GlobalEvent[]
}