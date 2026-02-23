from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, model_validator

from app.models import (
    UserRole, MandantKategorie, Abgabeweg, WorkflowStatus,
    Ampelstatus, ChecklistItemStatus, TicketStatus, TicketPrioritaet,
    EskalationStufe, EmailLogStatus, FristenRegeltyp, SonderaufgabeStatus,
    MandantKontaktRolle, GlobalEventTyp, WorkflowSchrittEbene, WorkflowSchrittTyp,
    WorkflowItemStatus, WorkflowItemDependencyTyp, StichtabCategory,
)

# ─────────────────────────────────────────
# Branche (Admin Stammdaten)
# ─────────────────────────────────────────

class BrancheBase(BaseModel):
    name: str
    beschreibung: Optional[str] = None
    faktor: float = 1.0
    soka_relevant: bool = False
    tags: Optional[str] = None  # JSON-encoded list

class BrancheCreate(BrancheBase):
    pass

class BrancheUpdate(BaseModel):
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    faktor: Optional[float] = None
    soka_relevant: Optional[bool] = None
    tags: Optional[str] = None
    ist_archiviert: Optional[bool] = None

class BrancheOut(BrancheBase):
    id: int
    ist_archiviert: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Ausgabeweg Config (Admin Stammdaten)
# ─────────────────────────────────────────

class AusgabewegConfigBase(BaseModel):
    name: str
    beschreibung: Optional[str] = None
    ist_aktiv: bool = True
    beeinflusst_workflow: bool = False
    zusatz_workflow_schritt: Optional[str] = None

class AusgabewegConfigCreate(AusgabewegConfigBase):
    pass

class AusgabewegConfigUpdate(BaseModel):
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    ist_aktiv: Optional[bool] = None
    beeinflusst_workflow: Optional[bool] = None
    zusatz_workflow_schritt: Optional[str] = None

class AusgabewegConfigOut(AusgabewegConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Ticket-Anhänge
# ─────────────────────────────────────────

class TicketAnhangOut(BaseModel):
    id: int
    ticket_id: int
    kommentar_id: Optional[int] = None
    dateiname: str
    dateityp: Optional[str] = None
    dateigroesse: Optional[int] = None
    speicherort: str
    hash: Optional[str] = None
    hochgeladen_von: Optional["UserShort"] = None
    ist_intern: bool
    ist_geloescht: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# SMTP-Konfiguration
# ─────────────────────────────────────────

class SmtpKonfigurationBase(BaseModel):
    name: str = "Standard"
    server: str
    port: int = 587
    tls_ssl: str = "starttls"
    auth_user: Optional[str] = None
    absender_email: str
    reply_to: Optional[str] = None
    ist_aktiv: bool = True

class SmtpKonfigurationCreate(SmtpKonfigurationBase):
    auth_password: Optional[str] = None

class SmtpKonfigurationUpdate(BaseModel):
    name: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    tls_ssl: Optional[str] = None
    auth_user: Optional[str] = None
    auth_password: Optional[str] = None
    absender_email: Optional[str] = None
    reply_to: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class SmtpKonfigurationOut(SmtpKonfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# IMAP-Konfiguration
# ─────────────────────────────────────────

class ImapKonfigurationBase(BaseModel):
    name: str = "Standard"
    server: str
    port: int = 993
    tls_ssl: str = "ssl"
    auth_user: Optional[str] = None
    postfach: str = "INBOX"
    ordner: Optional[str] = None
    polling_intervall_sekunden: int = 300
    zuordnung_methode: str = "betreff"
    ist_aktiv: bool = True

class ImapKonfigurationCreate(ImapKonfigurationBase):
    auth_password: Optional[str] = None

class ImapKonfigurationUpdate(BaseModel):
    name: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    tls_ssl: Optional[str] = None
    auth_user: Optional[str] = None
    auth_password: Optional[str] = None
    postfach: Optional[str] = None
    ordner: Optional[str] = None
    polling_intervall_sekunden: Optional[int] = None
    zuordnung_methode: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class ImapKonfigurationOut(ImapKonfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# System-Defaults
# ─────────────────────────────────────────

class SystemDefaultOut(BaseModel):
    id: int
    bereich: str
    name: str
    konfiguration: Optional[str] = None
    ist_aktiv: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Upload-Konfiguration
# ─────────────────────────────────────────

class UploadKonfigurationBase(BaseModel):
    max_dateigroesse_mb: int = 10
    erlaubte_dateitypen: str = '["pdf","doc","docx","xls","xlsx","csv","jpg","jpeg","png","txt","zip"]'

class UploadKonfigurationUpdate(BaseModel):
    max_dateigroesse_mb: Optional[int] = None
    erlaubte_dateitypen: Optional[str] = None

class UploadKonfigurationOut(UploadKonfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# ─────────────────────────────────────────
# Auth
# ─────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ─────────────────────────────────────────
# User
# ─────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.SACHBEARBEITER
    is_active: bool = True
    workload_limit: float = 100.0
    current_workload: float = 0.0
    total_points_earned: float = 0.0


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    workload_limit: Optional[float] = None
    current_workload: Optional[float] = None
    total_points_earned: Optional[float] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    is_archived: bool = False
    anonymisiert_am: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserShort(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Mandant
# ─────────────────────────────────────────

class MandantBase(BaseModel):
    name: str
    nummer: Optional[str] = None
    branche: Optional[str] = None
    ansprechpartner_name: Optional[str] = None
    ansprechpartner_email: Optional[str] = None
    ansprechpartner_telefon: Optional[str] = None
    lohnabschluss_tag: int = 15
    abgabeweg: Abgabeweg = Abgabeweg.EMAIL
    kategorie: MandantKategorie = MandantKategorie.B
    service_level: Optional[str] = None
    mitarbeiteranzahl: int = 1
    besonderheiten: Optional[str] = None
    sachbearbeiter_id: Optional[int] = None
    vertretung_id: Optional[int] = None
    stundensatz: Optional[float] = None
    monatspauschale: Optional[float] = None
    ist_aktiv: bool = True
    workflow_konfiguration: Optional[dict] = None  # { "optional_item_ids": [1, 2, 3] }


class MandantCreate(MandantBase):
    pass


class MandantUpdate(BaseModel):
    name: Optional[str] = None
    nummer: Optional[str] = None
    branche: Optional[str] = None
    ansprechpartner_name: Optional[str] = None
    ansprechpartner_email: Optional[str] = None
    ansprechpartner_telefon: Optional[str] = None
    lohnabschluss_tag: Optional[int] = None
    abgabeweg: Optional[Abgabeweg] = None
    kategorie: Optional[MandantKategorie] = None
    service_level: Optional[str] = None
    mitarbeiteranzahl: Optional[int] = None
    besonderheiten: Optional[str] = None
    sachbearbeiter_id: Optional[int] = None
    vertretung_id: Optional[int] = None
    stundensatz: Optional[float] = None
    monatspauschale: Optional[float] = None
    ist_aktiv: Optional[bool] = None
    fristenprofil_id: Optional[int] = None
    aenderung_zum: Optional[datetime] = None
    workflow_konfiguration: Optional[dict] = None


class MandantOut(MandantBase):
    id: int
    portal_user_id: Optional[int] = None
    sachbearbeiter: Optional[UserShort] = None
    vertretung: Optional[UserShort] = None
    branchen_liste: List[BrancheOut] = []
    aenderungen: List["MandantAenderungOut"] = []
    fristenprofil: Optional["FristenprofilOut"] = None
    kontakte: List["MandantKontaktOut"] = []
    notizen: List["MandantNotizOut"] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def deserialize_workflow_konfiguration(cls, data):
        import json
        if hasattr(data, '__dict__'):
            # SQLAlchemy model instance
            wf_konf = data.workflow_konfiguration
            if wf_konf and isinstance(wf_konf, str):
                data.workflow_konfiguration = json.loads(wf_konf)
        elif isinstance(data, dict) and 'workflow_konfiguration' in data:
            wf_konf = data.get('workflow_konfiguration')
            if wf_konf and isinstance(wf_konf, str):
                data['workflow_konfiguration'] = json.loads(wf_konf)
        return data


class MandantShort(BaseModel):
    id: int
    name: str
    nummer: Optional[str] = None
    kategorie: MandantKategorie
    ist_aktiv: bool

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Mandant Änderungen
# ─────────────────────────────────────────

class MandantAenderungBase(BaseModel):
    aenderung_zum: Optional[datetime] = None
    aenderungen: str  # JSON string

class MandantAenderungCreate(MandantAenderungBase):
    pass

class MandantAenderungOut(MandantAenderungBase):
    id: int
    mandant_id: int
    status: str
    erstellt_von: UserShort
    erstellt_am: datetime
    aktiviert_am: Optional[datetime] = None
    abgebrochen_am: Optional[datetime] = None
    abgebrochen_von: Optional[UserShort] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────# Fristenprofil
# ─────────────────────────────────────────

class FristenregelBase(BaseModel):
    fristart: str
    regeltyp: FristenRegeltyp
    regel_config: str  # JSON
    bundesland: Optional[str] = None
    interne_vorfrist_tage: int = 0
    ist_aktiv: bool = True

class FristenregelCreate(FristenregelBase):
    pass

class FristenregelUpdate(BaseModel):
    fristart: Optional[str] = None
    regeltyp: Optional[FristenRegeltyp] = None
    regel_config: Optional[str] = None
    bundesland: Optional[str] = None
    interne_vorfrist_tage: Optional[int] = None
    ist_aktiv: Optional[bool] = None

class FristenregelOut(FristenregelBase):
    id: int
    profil_id: int
    position: int

    model_config = {"from_attributes": True}


class FristenprofilBase(BaseModel):
    name: str
    ist_aktiv: bool = True

class FristenprofilCreate(FristenprofilBase):
    regeln: List[FristenregelCreate] = []

class FristenprofilUpdate(BaseModel):
    name: Optional[str] = None
    ist_aktiv: Optional[bool] = None
    regeln: Optional[List[FristenregelUpdate]] = None

class FristenprofilOut(FristenprofilBase):
    id: int
    mandant_id: int
    regeln: List[FristenregelOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Sonderaufgabe
# ─────────────────────────────────────────

class SonderaufgabeBase(BaseModel):
    mandant_id: Optional[int] = None
    monat: Optional[int] = None
    jahr: Optional[int] = None
    kategorie: str
    titel: str
    beschreibung: Optional[str] = None
    faellig_datum: Optional[datetime] = None
    verantwortlicher_id: Optional[int] = None
    punkte: float = 0.0

class SonderaufgabeCreate(SonderaufgabeBase):
    pass

class SonderaufgabeUpdate(BaseModel):
    mandant_id: Optional[int] = None
    monat: Optional[int] = None
    jahr: Optional[int] = None
    kategorie: Optional[str] = None
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    faellig_datum: Optional[datetime] = None
    status: Optional[SonderaufgabeStatus] = None
    verantwortlicher_id: Optional[int] = None
    punkte: Optional[float] = None

class SonderaufgabeOut(SonderaufgabeBase):
    id: int
    status: SonderaufgabeStatus
    erstellt_von: UserShort
    verantwortlicher: Optional[UserShort] = None
    created_at: datetime
    abgeschlossen_am: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# MandantKontakt
# ─────────────────────────────────────────

class MandantKontaktBase(BaseModel):
    rolle: MandantKontaktRolle
    name: str
    email: Optional[str] = None
    telefon: Optional[str] = None
    ist_aktiv: bool = True

class MandantKontaktCreate(MandantKontaktBase):
    pass

class MandantKontaktUpdate(BaseModel):
    rolle: Optional[MandantKontaktRolle] = None
    name: Optional[str] = None
    email: Optional[str] = None
    telefon: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class MandantKontaktOut(MandantKontaktBase):
    id: int
    mandant_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# MandantNotiz
# ─────────────────────────────────────────

class MandantNotizBase(BaseModel):
    inhalt: str

class MandantNotizCreate(MandantNotizBase):
    pass

class MandantNotizOut(MandantNotizBase):
    id: int
    mandant_id: int
    version: int
    erstellt_von: UserShort
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Workflow Phase
# ─────────────────────────────────────────

class WorkflowPhaseBase(BaseModel):
    position: int
    name: str
    icon: Optional[str] = None
    standard_frist_tag: Optional[int] = None
    ist_kernprozess: bool = False


class WorkflowPhaseCreate(WorkflowPhaseBase):
    pass


class WorkflowPhaseUpdate(BaseModel):
    position: Optional[int] = None
    name: Optional[str] = None
    icon: Optional[str] = None
    standard_frist_tag: Optional[int] = None
    ist_kernprozess: Optional[bool] = None


class WorkflowPhaseOut(WorkflowPhaseBase):
    id: int
    vorlage_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Workflow Item Dependency
# ─────────────────────────────────────────

class WorkflowVorlageItemDependencyBase(BaseModel):
    source_item_id: int
    target_item_id: int
    typ: WorkflowItemDependencyTyp
    beschreibung: Optional[str] = None


class WorkflowVorlageItemDependencyCreate(WorkflowVorlageItemDependencyBase):
    pass


class WorkflowVorlageItemDependencyUpdate(BaseModel):
    typ: Optional[WorkflowItemDependencyTyp] = None
    beschreibung: Optional[str] = None


class WorkflowVorlageItemDependencyOut(WorkflowVorlageItemDependencyBase):
    id: int
    vorlage_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Workflow Vorlage
# ─────────────────────────────────────────

class WorkflowVorlageItemBase(BaseModel):
    position: int
    titel: str
    beschreibung: Optional[str] = None
    verantwortlich_rolle: Optional[UserRole] = None
    faellig_offset_tage: int = 0
    ist_kernprozess: bool = False  # kernel process step (replaces hardcoded fields)
    ist_pflicht: bool = True
    ist_optional_pro_mandant: bool = False
    erfordert_dokument: bool = False
    erfordert_pruefung: bool = False
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: int = 0
    standard_punkte: float = 1.0


class WorkflowVorlageItemCreate(WorkflowVorlageItemBase):
    pass


class WorkflowVorlageItemOut(WorkflowVorlageItemBase):
    id: int
    vorlage_id: int
    phase_id: Optional[int] = None

    model_config = {"from_attributes": True}


class WorkflowVorlageBase(BaseModel):
    name: str
    beschreibung: Optional[str] = None
    branche: Optional[str] = None
    ist_standard: bool = False
    ist_onboarding: bool = False


class WorkflowVorlageCreate(WorkflowVorlageBase):
    items: List[WorkflowVorlageItemCreate] = []


class WorkflowVorlageUpdate(BaseModel):
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    branche: Optional[str] = None
    ist_standard: Optional[bool] = None


class WorkflowVorlageOut(WorkflowVorlageBase):
    id: int
    erstellt_von_id: Optional[int] = None
    created_at: datetime
    phasen: List[WorkflowPhaseOut] = []
    items: List[WorkflowVorlageItemOut] = []
    item_dependencies: List[WorkflowVorlageItemDependencyOut] = []

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Workflow Instanz
# ─────────────────────────────────────────

class WorkflowInstanzCreate(BaseModel):
    mandant_id: int
    vorlage_id: Optional[int] = None
    monat: int
    jahr: int
    sachbearbeiter_id: Optional[int] = None
    pruefer_id: Optional[int] = None
    notizen: Optional[str] = None


class WorkflowInstanzUpdate(BaseModel):
    status: Optional[WorkflowStatus] = None
    ampelstatus: Optional[Ampelstatus] = None
    sachbearbeiter_id: Optional[int] = None
    pruefer_id: Optional[int] = None
    unterlagen_eingegangen_am: Optional[datetime] = None
    unterlagen_eingegangen_von_id: Optional[int] = None
    probe_abrechnung_am: Optional[datetime] = None
    probe_abrechnung_von_id: Optional[int] = None
    probe_geprueft_am: Optional[datetime] = None
    probe_geprueft_von_id: Optional[int] = None
    mandant_freigabe_am: Optional[datetime] = None
    mandant_freigabe_von_id: Optional[int] = None
    endabrechnung_am: Optional[datetime] = None
    endabrechnung_von_id: Optional[int] = None
    versand_am: Optional[datetime] = None
    versand_von_id: Optional[int] = None
    abgeschlossen_am: Optional[datetime] = None
    abgeschlossen_von_id: Optional[int] = None
    wiedereroeffnet_begruendung: Optional[str] = None
    notizen: Optional[str] = None


class WorkflowItemUpdate(BaseModel):
    status: Optional[ChecklistItemStatus] = None
    notiz: Optional[str] = None
    zugewiesen_an_id: Optional[int] = None


class WorkflowItemOut(BaseModel):
    id: int
    instanz_id: int
    position: int
    titel: str
    beschreibung: Optional[str] = None
    schritttyp: Optional[str] = None
    verantwortlich_rolle: Optional[UserRole] = None
    zugewiesen_an: Optional[UserShort] = None
    faellig_datum: Optional[datetime] = None
    sla_warnung_ab: Optional[datetime] = None
    ist_pflicht: bool
    erfordert_dokument: bool
    erfordert_pruefung: bool
    fristart_referenz: Optional[str] = None
    status: ChecklistItemStatus
    phase_id: Optional[int] = None
    erledigt_am: Optional[datetime] = None
    erledigt_von: Optional[UserShort] = None
    started_at: Optional[datetime] = None
    actual_duration_minuten: Optional[int] = None
    notiz: Optional[str] = None
    punkte: float = 0.0
    ist_blockiert: bool = False
    blockiert_grund: Optional[str] = None
    blockiert_von_item_ids: Optional[List[int]] = None
    blockierung_seit: Optional[datetime] = None
    ist_ueberfaellig: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowInstanzOut(BaseModel):
    id: int
    mandant_id: int
    mandant: Optional[MandantShort] = None
    vorlage_id: Optional[int] = None
    monat: int
    jahr: int
    status: WorkflowStatus
    ampelstatus: Ampelstatus
    sachbearbeiter: Optional[UserShort] = None
    pruefer: Optional[UserShort] = None
    
    # SLA tracking
    sla_deadline: Optional[datetime] = None
    sla_status: Optional[str] = None
    
    # Key process steps (backward compat)
    unterlagen_eingegangen_am: Optional[datetime] = None
    unterlagen_eingegangen_von: Optional[UserShort] = None
    unterlagen_faellig: Optional[datetime] = None
    probe_abrechnung_am: Optional[datetime] = None
    probe_abrechnung_von: Optional[UserShort] = None
    probe_abrechnung_faellig: Optional[datetime] = None
    probe_geprueft_am: Optional[datetime] = None
    probe_geprueft_von: Optional[UserShort] = None
    probe_geprueft_faellig: Optional[datetime] = None
    mandant_freigabe_am: Optional[datetime] = None
    mandant_freigabe_von: Optional[UserShort] = None
    mandant_freigabe_faellig: Optional[datetime] = None
    endabrechnung_am: Optional[datetime] = None
    endabrechnung_von: Optional[UserShort] = None
    endabrechnung_faellig: Optional[datetime] = None
    versand_am: Optional[datetime] = None
    versand_von: Optional[UserShort] = None
    versand_faellig: Optional[datetime] = None
    abgeschlossen_am: Optional[datetime] = None
    abgeschlossen_von: Optional[UserShort] = None
    abgeschlossen_faellig: Optional[datetime] = None
    
    # Time tracking
    notizen: Optional[str] = None
    punkte: float = 0.0
    created_at: datetime
    started_at: Optional[datetime] = None
    durchlaufzeit_stunden: Optional[float] = None
    verzoegerung_tage: Optional[int] = None
    
    items: List[WorkflowItemOut] = []

    model_config = {"from_attributes": True}


class WorkflowInstanzShort(BaseModel):
    id: int
    mandant_id: int
    monat: int
    jahr: int
    status: WorkflowStatus
    ampelstatus: Ampelstatus
    mandant: Optional[MandantShort] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Ticket
# ─────────────────────────────────────────

class TicketKommentarCreate(BaseModel):
    inhalt: str
    ist_intern: bool = False
    zitat_id: Optional[int] = None


class TicketKommentarOut(BaseModel):
    id: int
    ticket_id: int
    autor: UserShort
    inhalt: str
    ist_intern: bool
    zitat_id: Optional[int] = None
    anhaenge: List[TicketAnhangOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketBase(BaseModel):
    mandant_id: int
    workflow_instanz_id: Optional[int] = None
    workflow_item_id: Optional[int] = None
    titel: str
    beschreibung: Optional[str] = None
    prioritaet: TicketPrioritaet = TicketPrioritaet.NORMAL
    kategorie: Optional[str] = None
    unterkategorie: Optional[str] = None
    faellig_bis: Optional[datetime] = None
    zugewiesen_an_id: Optional[int] = None
    monat: Optional[int] = None
    jahr: Optional[int] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    status: Optional[TicketStatus] = None
    prioritaet: Optional[TicketPrioritaet] = None
    kategorie: Optional[str] = None
    unterkategorie: Optional[str] = None
    faellig_bis: Optional[datetime] = None
    zugewiesen_an_id: Optional[int] = None
    eskalationsstufe: Optional[EskalationStufe] = None
    wiedervorlage_datum: Optional[datetime] = None
    abbruch_grund: Optional[str] = None


class TicketOut(TicketBase):
    id: int
    status: TicketStatus
    eskalationsstufe: Optional[EskalationStufe] = None
    wiedervorlage_datum: Optional[datetime] = None
    abbruch_grund: Optional[str] = None
    erstellt_von: UserShort
    zugewiesen_an: Optional[UserShort] = None
    mandant: MandantShort
    geschlossen_am: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    kommentare: List[TicketKommentarOut] = []
    anhaenge: List[TicketAnhangOut] = []

    model_config = {"from_attributes": True}


class TicketShort(BaseModel):
    id: int
    titel: str
    status: TicketStatus
    prioritaet: TicketPrioritaet
    eskalationsstufe: Optional[EskalationStufe] = None
    mandant: MandantShort
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# SLA Konfiguration
# ─────────────────────────────────────────

class SLAKonfigurationBase(BaseModel):
    kategorie: str
    prioritaet: Optional[TicketPrioritaet] = None
    sla_stunden: int = 48
    eskalation_stufe1_stunden: int = 72
    eskalation_stufe2_stunden: int = 96


class SLAKonfigurationCreate(SLAKonfigurationBase):
    pass


class SLAKonfigurationOut(SLAKonfigurationBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    objekt_typ: str
    objekt_id: Optional[int] = None
    mandant_id: Optional[int] = None
    monat: Optional[int] = None
    jahr: Optional[int] = None
    aktionstyp: str
    alter_wert: Optional[str] = None
    neuer_wert: Optional[str] = None
    benutzer_id: Optional[int] = None
    benutzer: Optional[UserShort] = None
    benutzerrolle: Optional[str] = None
    zeitstempel: datetime
    ip_adresse: Optional[str] = None
    beschreibung: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Email Templates
# ─────────────────────────────────────────

class EmailTemplateBase(BaseModel):
    name: str
    betreff: str
    html_inhalt: str
    text_inhalt: Optional[str] = None
    beschreibung: Optional[str] = None
    typ: Optional[str] = None
    ist_aktiv: bool = True
    reihenfolge: int = 0
    verzoegerung_tage: int = 0


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    betreff: Optional[str] = None
    html_inhalt: Optional[str] = None
    text_inhalt: Optional[str] = None
    beschreibung: Optional[str] = None
    typ: Optional[str] = None
    ist_aktiv: Optional[bool] = None
    reihenfolge: Optional[int] = None
    verzoegerung_tage: Optional[int] = None


class EmailTemplateOut(EmailTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailLogOut(BaseModel):
    id: int
    template_id: Optional[int] = None
    mandant_id: int
    empfaenger: str
    betreff: str
    status: EmailLogStatus
    gesendet_am: datetime
    fehler: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Dokument
# ─────────────────────────────────────────

class DokumentOut(BaseModel):
    id: int
    mandant_id: int
    workflow_instanz_id: Optional[int] = None
    workflow_item_id: Optional[int] = None
    name: str
    dateityp: Optional[str] = None
    dateigroesse: Optional[int] = None
    speicherort: Optional[str] = None
    kategorie: Optional[str] = None
    notiz: Optional[str] = None
    hochgeladen_von: Optional[UserShort] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Eskalation
# ─────────────────────────────────────────

class EskalationOut(BaseModel):
    id: int
    mandant_id: int
    workflow_instanz_id: Optional[int] = None
    eskalationsstufe: EskalationStufe
    eskaliert_an: Optional[UserShort] = None
    ausgeloest_am: datetime
    notiz: Optional[str] = None
    ist_geloest: bool
    geloest_am: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────

class DashboardStats(BaseModel):
    mandanten_gesamt: int
    mandanten_aktiv: int
    workflows_offen: int
    workflows_in_bearbeitung: int
    workflows_eskaliert: int
    tickets_offen: int
    tickets_dringend: int
    ampel_rot: int
    ampel_gelb: int
    ampel_gruen: int


class MandantAmpelInfo(BaseModel):
    mandant_id: int
    mandant_name: str
    mandant_kategorie: MandantKategorie
    workflow_id: Optional[int] = None
    monat: Optional[int] = None
    jahr: Optional[int] = None
    status: Optional[WorkflowStatus] = None
    ampelstatus: Ampelstatus
    sachbearbeiter: Optional[UserShort] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Dashboard "Mein Tag" Sections
# ─────────────────────────────────────────

class KritischInfo(BaseModel):
    mandant_id: int
    mandant_name: str
    mandant_kategorie: MandantKategorie
    workflow_id: int
    monat: int
    jahr: int
    naechster_stichtag: Optional[str] = None
    stichtag_typ: Optional[str] = None
    ampelstatus: Ampelstatus
    sachbearbeiter: Optional[UserShort] = None
    blocker: Optional[str] = None

    model_config = {"from_attributes": True}


class WartetAufMandantInfo(BaseModel):
    mandant_id: int
    mandant_name: str
    workflow_id: int
    monat: int
    jahr: int
    ticket_id: Optional[int] = None
    ticket_titel: Optional[str] = None
    sachbearbeiter: Optional[UserShort] = None
    wartet_seit: Optional[str] = None

    model_config = {"from_attributes": True}


class MeineArbeitItem(BaseModel):
    typ: str  # 'workflow_schritt' or 'sonderaufgabe'
    id: int
    titel: str
    mandant_id: int
    mandant_name: str
    monat: Optional[int] = None
    jahr: Optional[int] = None
    faellig_datum: Optional[str] = None
    punkte: Optional[float] = None
    prioritaet: Optional[str] = None

    model_config = {"from_attributes": True}


class DashboardMeinTag(BaseModel):
    kritisch: List[KritischInfo] = []
    wartet_auf_mandant: List[WartetAufMandantInfo] = []
    meine_arbeit: List[MeineArbeitItem] = []

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# FristenVorlage (Default Deadline Templates)
# ─────────────────────────────────────────

class FristenVorlageBase(BaseModel):
    code: str
    name: str
    beschreibung: Optional[str] = None
    regeltyp: FristenRegeltyp
    regel_config: str  # JSON
    default_interne_vorfrist_tage: int = 2
    ist_jahresbezogen: bool = False
    ist_ereignisbasiert: bool = False
    branchenfilter: Optional[str] = None
    anmeldezeitraum: Optional[str] = None
    ist_aktiv: bool = True

class FristenVorlageCreate(FristenVorlageBase):
    pass

class FristenVorlageOut(FristenVorlageBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# WorkflowSchrittTyp (Admin-definable)
# ─────────────────────────────────────────

class WorkflowSchrittTypBase(BaseModel):
    name: str
    beschreibung: Optional[str] = None
    ist_pflicht: bool = True
    standard_rolle: Optional[UserRole] = None
    abhaengigkeit_von: Optional[str] = None
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: int = 0
    standard_punkte: float = 1.0
    ist_aktiv: bool = True

class WorkflowSchrittTypCreate(WorkflowSchrittTypBase):
    pass

class WorkflowSchrittTypUpdate(BaseModel):
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    ist_pflicht: Optional[bool] = None
    standard_rolle: Optional[UserRole] = None
    abhaengigkeit_von: Optional[str] = None
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: Optional[int] = None
    standard_punkte: Optional[float] = None
    ist_aktiv: Optional[bool] = None

class WorkflowSchrittTypOut(WorkflowSchrittTypBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# MandantWorkflowSchritt (per-mandant activation)
# ─────────────────────────────────────────

class MandantWorkflowSchrittBase(BaseModel):
    schritt_typ_id: int
    ist_aktiv: bool = True
    aenderung_zum: Optional[datetime] = None

class MandantWorkflowSchrittCreate(MandantWorkflowSchrittBase):
    pass

class MandantWorkflowSchrittOut(MandantWorkflowSchrittBase):
    id: int
    mandant_id: int
    schritt_typ: WorkflowSchrittTypOut
    erstellt_von: Optional[UserShort] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# PunkteKonfiguration (Workload Point Rules)
# ─────────────────────────────────────────

class PunkteKonfigurationBase(BaseModel):
    name: str
    kategorie_basis: str  # JSON
    mitarbeiter_stufen: str  # JSON
    branchen_faktoren: Optional[str] = None
    zusatzmodul_punkte: Optional[str] = None
    ist_aktiv: bool = True

class PunkteKonfigurationCreate(PunkteKonfigurationBase):
    pass

class PunkteKonfigurationUpdate(BaseModel):
    name: Optional[str] = None
    kategorie_basis: Optional[str] = None
    mitarbeiter_stufen: Optional[str] = None
    branchen_faktoren: Optional[str] = None
    zusatzmodul_punkte: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class PunkteKonfigurationOut(PunkteKonfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# One-Screen: Mandant-Month Combined View
# ─────────────────────────────────────────

class FristStatusOut(BaseModel):
    fristart: str
    name: str
    externer_stichtag: Optional[str] = None   # date string
    interne_vorfrist: Optional[str] = None    # date string
    ampel: str = "gruen"                       # gruen/gelb/rot
    betroffene_schritte: List[str] = []        # titles of affected workflow steps

class MandantMonatOneScreen(BaseModel):
    mandant_id: int
    mandant_name: str
    monat: int
    jahr: int
    workflow: Optional[WorkflowInstanzOut] = None
    tickets: List[TicketShort] = []
    sonderaufgaben: List[SonderaufgabeOut] = []
    fristen: List[FristStatusOut] = []
    blocker: List[str] = []                    # descriptions of current blockers


# ─────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────

class MitarbeiterPunkteReport(BaseModel):
    user_id: int
    full_name: str
    email: str
    role: UserRole
    punkte_gesamt: float = 0.0
    punkte_workflows: float = 0.0
    punkte_sonderaufgaben: float = 0.0
    mandanten_count: int = 0

class MandantPunkteDetail(BaseModel):
    mandant_id: int
    mandant_name: str
    monat: int
    jahr: int
    punkte: float = 0.0
    schritte: List[str] = []
    sonderaufgaben_punkte: float = 0.0


# ─────────────────────────────────────────
# Tenant (Multi-Tenancy)
# ─────────────────────────────────────────

class TenantBase(BaseModel):
    name: str
    code: str
    beschreibung: Optional[str] = None
    logo_url: Optional[str] = None
    primaerfarbe: Optional[str] = None
    konfiguration: Optional[str] = None  # JSON
    ist_aktiv: bool = True

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    beschreibung: Optional[str] = None
    logo_url: Optional[str] = None
    primaerfarbe: Optional[str] = None
    konfiguration: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class TenantOut(TenantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Abrechnungsfirma
# ─────────────────────────────────────────

class AbrechnungsfirmaBase(BaseModel):
    name: str
    code: str
    beschreibung: Optional[str] = None
    strasse: Optional[str] = None
    plz: Optional[str] = None
    ort: Optional[str] = None
    land: str = "Deutschland"
    telefon: Optional[str] = None
    email: Optional[str] = None
    steuernummer: Optional[str] = None
    ustid: Optional[str] = None
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    workflow_konfiguration: Optional[str] = None  # JSON
    ist_aktiv: bool = True

class AbrechnungsfirmaCreate(AbrechnungsfirmaBase):
    tenant_id: int

class AbrechnungsfirmaUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    beschreibung: Optional[str] = None
    strasse: Optional[str] = None
    plz: Optional[str] = None
    ort: Optional[str] = None
    land: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    steuernummer: Optional[str] = None
    ustid: Optional[str] = None
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    workflow_konfiguration: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class AbrechnungsfirmaOut(AbrechnungsfirmaBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Global Event (Jahreswechsel, Mindestlohnerhöhung, etc.)
# ─────────────────────────────────────────

class GlobalEventSchrittBase(BaseModel):
    position: int
    titel: str
    beschreibung: Optional[str] = None
    schritttyp: WorkflowSchrittTyp = WorkflowSchrittTyp.VERARBEITUNG
    einfuege_position: str = "vor_abschluss"
    referenz_schritt_id: Optional[int] = None
    faellig_offset_tage: int = 0
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: int = 0
    ist_pflicht: bool = True
    erfordert_dokument: bool = False
    erfordert_pruefung: bool = False
    verantwortlich_rolle: Optional[UserRole] = None
    standard_punkte: float = 1.0
    anleitung: Optional[str] = None
    ist_aktiv: bool = True

class GlobalEventSchrittCreate(GlobalEventSchrittBase):
    pass

class GlobalEventSchrittUpdate(BaseModel):
    position: Optional[int] = None
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    schritttyp: Optional[WorkflowSchrittTyp] = None
    einfuege_position: Optional[str] = None
    referenz_schritt_id: Optional[int] = None
    faellig_offset_tage: Optional[int] = None
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: Optional[int] = None
    ist_pflicht: Optional[bool] = None
    erfordert_dokument: Optional[bool] = None
    erfordert_pruefung: Optional[bool] = None
    verantwortlich_rolle: Optional[UserRole] = None
    standard_punkte: Optional[float] = None
    anleitung: Optional[str] = None
    ist_aktiv: Optional[bool] = None

class GlobalEventSchrittOut(GlobalEventSchrittBase):
    id: int
    event_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GlobalEventBase(BaseModel):
    typ: GlobalEventTyp
    name: str
    beschreibung: Optional[str] = None
    gueltig_von: datetime
    gueltig_bis: Optional[datetime] = None
    betroffene_monate: Optional[str] = None  # JSON
    mandanten_filter: Optional[str] = None  # JSON
    prioritaet: int = 0
    ist_aktiv: bool = True

class GlobalEventCreate(GlobalEventBase):
    tenant_id: Optional[int] = None
    schritte: List[GlobalEventSchrittCreate] = []

class GlobalEventUpdate(BaseModel):
    typ: Optional[GlobalEventTyp] = None
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    gueltig_von: Optional[datetime] = None
    gueltig_bis: Optional[datetime] = None
    betroffene_monate: Optional[str] = None
    mandanten_filter: Optional[str] = None
    prioritaet: Optional[int] = None
    ist_aktiv: Optional[bool] = None
    ist_abgeschlossen: Optional[bool] = None

class GlobalEventOut(GlobalEventBase):
    id: int
    tenant_id: Optional[int] = None
    ist_abgeschlossen: bool = False
    erstellt_von: Optional[UserShort] = None
    schritte: List[GlobalEventSchrittOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Branchenspezifische Workflow-Schritte
# ─────────────────────────────────────────

class BranchenWorkflowSchrittBase(BaseModel):
    position: int
    titel: str
    beschreibung: Optional[str] = None
    schritttyp: WorkflowSchrittTyp = WorkflowSchrittTyp.VERARBEITUNG
    einfuege_position: str = "vor_abschluss"
    referenz_schritt_id: Optional[int] = None
    faellig_offset_tage: int = 0
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: int = 0
    ist_pflicht: bool = True
    ist_optional_pro_mandant: bool = False
    erfordert_dokument: bool = False
    erfordert_pruefung: bool = False
    verantwortlich_rolle: Optional[UserRole] = None
    standard_punkte: float = 1.0
    gueltig_von: Optional[datetime] = None
    gueltig_bis: Optional[datetime] = None
    ist_aktiv: bool = True

class BranchenWorkflowSchrittCreate(BranchenWorkflowSchrittBase):
    branche_id: int

class BranchenWorkflowSchrittUpdate(BaseModel):
    position: Optional[int] = None
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    schritttyp: Optional[WorkflowSchrittTyp] = None
    einfuege_position: Optional[str] = None
    referenz_schritt_id: Optional[int] = None
    faellig_offset_tage: Optional[int] = None
    fristart_referenz: Optional[str] = None
    fristart_offset_tage: Optional[int] = None
    ist_pflicht: Optional[bool] = None
    ist_optional_pro_mandant: Optional[bool] = None
    erfordert_dokument: Optional[bool] = None
    erfordert_pruefung: Optional[bool] = None
    verantwortlich_rolle: Optional[UserRole] = None
    standard_punkte: Optional[float] = None
    gueltig_von: Optional[datetime] = None
    gueltig_bis: Optional[datetime] = None
    ist_aktiv: Optional[bool] = None

class BranchenWorkflowSchrittOut(BranchenWorkflowSchrittBase):
    id: int
    branche_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Workflow Item Herkunft (Tracking)
# ─────────────────────────────────────────

class WorkflowItemHerkunftOut(BaseModel):
    id: int
    workflow_item_id: int
    ebene: WorkflowSchrittEbene
    vorlage_item_id: Optional[int] = None
    branchen_schritt_id: Optional[int] = None
    mandant_schritt_id: Optional[int] = None
    global_event_schritt_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Erweiterter Workflow-Instanz mit Herkunft
# ─────────────────────────────────────────

class WorkflowItemMitHerkunftOut(WorkflowItemOut):
    herkunft: Optional[WorkflowItemHerkunftOut] = None
    ebene: Optional[WorkflowSchrittEbene] = None  # Convenience field


class WorkflowInstanzMitHerkunftOut(WorkflowInstanzOut):
    items: List[WorkflowItemMitHerkunftOut] = []
    global_events: List[GlobalEventOut] = []
