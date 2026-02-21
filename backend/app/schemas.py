from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models import (
    UserRole, MandantKategorie, Abgabeweg, WorkflowStatus,
    Ampelstatus, ChecklistItemStatus, TicketStatus, TicketPrioritaet, EskalationStufe
)

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


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
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


class MandantOut(MandantBase):
    id: int
    portal_user_id: Optional[int] = None
    sachbearbeiter: Optional[UserShort] = None
    vertretung: Optional[UserShort] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MandantShort(BaseModel):
    id: int
    name: str
    nummer: Optional[str] = None
    kategorie: MandantKategorie
    ist_aktiv: bool

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
    ist_pflicht: bool = True
    erfordert_dokument: bool = False
    erfordert_pruefung: bool = False


class WorkflowVorlageItemCreate(WorkflowVorlageItemBase):
    pass


class WorkflowVorlageItemOut(WorkflowVorlageItemBase):
    id: int
    vorlage_id: int

    model_config = {"from_attributes": True}


class WorkflowVorlageBase(BaseModel):
    name: str
    beschreibung: Optional[str] = None
    branche: Optional[str] = None
    ist_standard: bool = False


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
    items: List[WorkflowVorlageItemOut] = []

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
    probe_abrechnung_am: Optional[datetime] = None
    probe_geprueft_am: Optional[datetime] = None
    mandant_freigabe_am: Optional[datetime] = None
    endabrechnung_am: Optional[datetime] = None
    versand_am: Optional[datetime] = None
    abgeschlossen_am: Optional[datetime] = None
    notizen: Optional[str] = None


class WorkflowItemUpdate(BaseModel):
    status: Optional[ChecklistItemStatus] = None
    notiz: Optional[str] = None


class WorkflowItemOut(BaseModel):
    id: int
    instanz_id: int
    position: int
    titel: str
    beschreibung: Optional[str] = None
    verantwortlich_rolle: Optional[UserRole] = None
    faellig_datum: Optional[datetime] = None
    ist_pflicht: bool
    erfordert_dokument: bool
    erfordert_pruefung: bool
    status: ChecklistItemStatus
    erledigt_am: Optional[datetime] = None
    erledigt_von: Optional[UserShort] = None
    notiz: Optional[str] = None

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
    unterlagen_eingegangen_am: Optional[datetime] = None
    probe_abrechnung_am: Optional[datetime] = None
    probe_geprueft_am: Optional[datetime] = None
    mandant_freigabe_am: Optional[datetime] = None
    endabrechnung_am: Optional[datetime] = None
    versand_am: Optional[datetime] = None
    abgeschlossen_am: Optional[datetime] = None
    notizen: Optional[str] = None
    created_at: datetime
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


class TicketKommentarOut(BaseModel):
    id: int
    ticket_id: int
    autor: UserShort
    inhalt: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketBase(BaseModel):
    mandant_id: int
    workflow_instanz_id: Optional[int] = None
    titel: str
    beschreibung: Optional[str] = None
    prioritaet: TicketPrioritaet = TicketPrioritaet.NORMAL
    kategorie: Optional[str] = None
    faellig_bis: Optional[datetime] = None
    zugewiesen_an_id: Optional[int] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    status: Optional[TicketStatus] = None
    prioritaet: Optional[TicketPrioritaet] = None
    kategorie: Optional[str] = None
    faellig_bis: Optional[datetime] = None
    zugewiesen_an_id: Optional[int] = None


class TicketOut(TicketBase):
    id: int
    status: TicketStatus
    erstellt_von: UserShort
    zugewiesen_an: Optional[UserShort] = None
    mandant: MandantShort
    geschlossen_am: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    kommentare: List[TicketKommentarOut] = []

    model_config = {"from_attributes": True}


class TicketShort(BaseModel):
    id: int
    titel: str
    status: TicketStatus
    prioritaet: TicketPrioritaet
    mandant: MandantShort
    created_at: datetime

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
