import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float
)
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────────────────────
# Enums
# ─────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEAMLEITUNG = "teamleitung"
    SACHBEARBEITER = "sachbearbeiter"
    PRUEFER = "pruefer"
    MANDANT = "mandant"


class MandantKategorie(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class Abgabeweg(str, enum.Enum):
    EMAIL = "email"
    POST = "post"
    PORTAL = "portal"
    FAX = "fax"


class WorkflowStatus(str, enum.Enum):
    OFFEN = "offen"
    IN_BEARBEITUNG = "in_bearbeitung"
    WARTE_FREIGABE = "warte_freigabe"
    ABGESCHLOSSEN = "abgeschlossen"
    ESKALIERT = "eskaliert"


class Ampelstatus(str, enum.Enum):
    GRUEN = "gruen"
    GELB = "gelb"
    ROT = "rot"


class ChecklistItemStatus(str, enum.Enum):
    OFFEN = "offen"
    ERLEDIGT = "erledigt"
    UEBERSPRUNGEN = "uebersprungen"
    BLOCKIERT = "blockiert"


class TicketStatus(str, enum.Enum):
    OFFEN = "offen"
    IN_BEARBEITUNG = "in_bearbeitung"
    BEANTWORTET = "beantwortet"
    GESCHLOSSEN = "geschlossen"


class TicketPrioritaet(str, enum.Enum):
    NIEDRIG = "niedrig"
    NORMAL = "normal"
    HOCH = "hoch"
    DRINGEND = "dringend"


class EskalationStufe(str, enum.Enum):
    REMINDER = "reminder"
    TEAMLEITUNG = "teamleitung"
    LEITUNG = "leitung"


# ─────────────────────────────────────────
# User
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SACHBEARBEITER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mandanten_als_sachbearbeiter = relationship(
        "Mandant", back_populates="sachbearbeiter", foreign_keys="Mandant.sachbearbeiter_id"
    )
    mandanten_als_vertretung = relationship(
        "Mandant", back_populates="vertretung", foreign_keys="Mandant.vertretung_id"
    )
    mandant_portal = relationship("Mandant", back_populates="portal_user", foreign_keys="Mandant.portal_user_id")
    tickets_erstellt = relationship("Ticket", back_populates="erstellt_von", foreign_keys="Ticket.erstellt_von_id")
    ticket_kommentare = relationship("TicketKommentar", back_populates="autor")
    workflow_items_erledigt = relationship("WorkflowItem", back_populates="erledigt_von")
    eskalationen = relationship("EskalationLog", back_populates="eskaliert_an", foreign_keys="EskalationLog.eskaliert_an_id")
    dokumente = relationship("Dokument", back_populates="hochgeladen_von")


# ─────────────────────────────────────────
# Mandant
# ─────────────────────────────────────────

class Mandant(Base):
    __tablename__ = "mandanten"

    id = Column(Integer, primary_key=True, index=True)
    nummer = Column(String, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    branche = Column(String)

    # Ansprechpartner
    ansprechpartner_name = Column(String)
    ansprechpartner_email = Column(String)
    ansprechpartner_telefon = Column(String)

    # Fristen & Organisation
    lohnabschluss_tag = Column(Integer, default=15)  # day of month
    abgabeweg = Column(Enum(Abgabeweg), default=Abgabeweg.EMAIL)
    kategorie = Column(Enum(MandantKategorie), default=MandantKategorie.B)
    service_level = Column(String)
    mitarbeiteranzahl = Column(Integer, default=1)
    besonderheiten = Column(Text)

    # Zuordnungen
    sachbearbeiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vertretung_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    portal_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Aufwand / Kalkulation
    stundensatz = Column(Float)
    monatspauschale = Column(Float)

    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sachbearbeiter = relationship("User", back_populates="mandanten_als_sachbearbeiter", foreign_keys=[sachbearbeiter_id])
    vertretung = relationship("User", back_populates="mandanten_als_vertretung", foreign_keys=[vertretung_id])
    portal_user = relationship("User", back_populates="mandant_portal", foreign_keys=[portal_user_id])
    workflow_instanzen = relationship("WorkflowInstanz", back_populates="mandant")
    tickets = relationship("Ticket", back_populates="mandant")
    dokumente = relationship("Dokument", back_populates="mandant")
    eskalationen = relationship("EskalationLog", back_populates="mandant")


# ─────────────────────────────────────────
# Workflow Template
# ─────────────────────────────────────────

class WorkflowVorlage(Base):
    __tablename__ = "workflow_vorlagen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    beschreibung = Column(Text)
    branche = Column(String)  # optional branche filter
    ist_standard = Column(Boolean, default=False)
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("WorkflowVorlageItem", back_populates="vorlage", order_by="WorkflowVorlageItem.position")
    instanzen = relationship("WorkflowInstanz", back_populates="vorlage")


class WorkflowVorlageItem(Base):
    __tablename__ = "workflow_vorlage_items"

    id = Column(Integer, primary_key=True, index=True)
    vorlage_id = Column(Integer, ForeignKey("workflow_vorlagen.id"), nullable=False)
    position = Column(Integer, nullable=False)
    titel = Column(String, nullable=False)
    beschreibung = Column(Text)
    verantwortlich_rolle = Column(Enum(UserRole))
    faellig_offset_tage = Column(Integer, default=0)  # days after month start
    ist_pflicht = Column(Boolean, default=True)
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)  # 4-eyes

    vorlage = relationship("WorkflowVorlage", back_populates="items")


# ─────────────────────────────────────────
# Workflow Instanz (monthly)
# ─────────────────────────────────────────

class WorkflowInstanz(Base):
    __tablename__ = "workflow_instanzen"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    vorlage_id = Column(Integer, ForeignKey("workflow_vorlagen.id"), nullable=True)
    monat = Column(Integer, nullable=False)   # 1-12
    jahr = Column(Integer, nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.OFFEN)
    ampelstatus = Column(Enum(Ampelstatus), default=Ampelstatus.GRUEN)

    sachbearbeiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pruefer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps for key process steps
    unterlagen_eingegangen_am = Column(DateTime, nullable=True)
    probe_abrechnung_am = Column(DateTime, nullable=True)
    probe_geprueft_am = Column(DateTime, nullable=True)
    mandant_freigabe_am = Column(DateTime, nullable=True)
    endabrechnung_am = Column(DateTime, nullable=True)
    versand_am = Column(DateTime, nullable=True)
    abgeschlossen_am = Column(DateTime, nullable=True)

    notizen = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mandant = relationship("Mandant", back_populates="workflow_instanzen")
    vorlage = relationship("WorkflowVorlage", back_populates="instanzen")
    sachbearbeiter = relationship("User", foreign_keys=[sachbearbeiter_id])
    pruefer = relationship("User", foreign_keys=[pruefer_id])
    items = relationship("WorkflowItem", back_populates="instanz", order_by="WorkflowItem.position")
    tickets = relationship("Ticket", back_populates="workflow_instanz")
    dokumente = relationship("Dokument", back_populates="workflow_instanz")
    eskalationen = relationship("EskalationLog", back_populates="workflow_instanz")


class WorkflowItem(Base):
    __tablename__ = "workflow_items"

    id = Column(Integer, primary_key=True, index=True)
    instanz_id = Column(Integer, ForeignKey("workflow_instanzen.id"), nullable=False)
    vorlage_item_id = Column(Integer, ForeignKey("workflow_vorlage_items.id"), nullable=True)
    position = Column(Integer, nullable=False)
    titel = Column(String, nullable=False)
    beschreibung = Column(Text)
    verantwortlich_rolle = Column(Enum(UserRole))
    faellig_datum = Column(DateTime, nullable=True)
    ist_pflicht = Column(Boolean, default=True)
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)

    status = Column(Enum(ChecklistItemStatus), default=ChecklistItemStatus.OFFEN)
    erledigt_am = Column(DateTime, nullable=True)
    erledigt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notiz = Column(Text)

    instanz = relationship("WorkflowInstanz", back_populates="items")
    erledigt_von = relationship("User", back_populates="workflow_items_erledigt")
    dokumente = relationship("Dokument", back_populates="workflow_item")


# ─────────────────────────────────────────
# Ticket (Rückfragen)
# ─────────────────────────────────────────

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    workflow_instanz_id = Column(Integer, ForeignKey("workflow_instanzen.id"), nullable=True)
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    zugewiesen_an_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    titel = Column(String, nullable=False)
    beschreibung = Column(Text)
    status = Column(Enum(TicketStatus), default=TicketStatus.OFFEN)
    prioritaet = Column(Enum(TicketPrioritaet), default=TicketPrioritaet.NORMAL)
    kategorie = Column(String)

    faellig_bis = Column(DateTime, nullable=True)
    geschlossen_am = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mandant = relationship("Mandant", back_populates="tickets")
    workflow_instanz = relationship("WorkflowInstanz", back_populates="tickets")
    erstellt_von = relationship("User", back_populates="tickets_erstellt", foreign_keys=[erstellt_von_id])
    zugewiesen_an = relationship("User", foreign_keys=[zugewiesen_an_id])
    kommentare = relationship("TicketKommentar", back_populates="ticket")


class TicketKommentar(Base):
    __tablename__ = "ticket_kommentare"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    autor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    inhalt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="kommentare")
    autor = relationship("User", back_populates="ticket_kommentare")


# ─────────────────────────────────────────
# Dokument
# ─────────────────────────────────────────

class Dokument(Base):
    __tablename__ = "dokumente"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    workflow_instanz_id = Column(Integer, ForeignKey("workflow_instanzen.id"), nullable=True)
    workflow_item_id = Column(Integer, ForeignKey("workflow_items.id"), nullable=True)
    hochgeladen_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    name = Column(String, nullable=False)
    dateityp = Column(String)
    dateigroesse = Column(Integer)  # bytes
    speicherort = Column(String)    # path or URL
    kategorie = Column(String)
    notiz = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    mandant = relationship("Mandant", back_populates="dokumente")
    workflow_instanz = relationship("WorkflowInstanz", back_populates="dokumente")
    workflow_item = relationship("WorkflowItem", back_populates="dokumente")
    hochgeladen_von = relationship("User", back_populates="dokumente")


# ─────────────────────────────────────────
# Eskalation Log
# ─────────────────────────────────────────

class EskalationLog(Base):
    __tablename__ = "eskalation_logs"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    workflow_instanz_id = Column(Integer, ForeignKey("workflow_instanzen.id"), nullable=True)
    eskalationsstufe = Column(Enum(EskalationStufe), nullable=False)
    eskaliert_an_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ausgeloest_am = Column(DateTime, default=datetime.utcnow)
    notiz = Column(Text)
    ist_geloest = Column(Boolean, default=False)
    geloest_am = Column(DateTime, nullable=True)

    mandant = relationship("Mandant", back_populates="eskalationen")
    workflow_instanz = relationship("WorkflowInstanz", back_populates="eskalationen")
    eskaliert_an = relationship("User", back_populates="eskalationen", foreign_keys=[eskaliert_an_id])
