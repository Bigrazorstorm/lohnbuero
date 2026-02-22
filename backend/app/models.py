import enum
import json
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float, Table
)
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────────────────────
# Association Tables
# ─────────────────────────────────────────

mandant_branchen = Table(
    "mandant_branchen",
    Base.metadata,
    Column("mandant_id", Integer, ForeignKey("mandanten.id"), primary_key=True),
    Column("branche_id", Integer, ForeignKey("branchen.id"), primary_key=True),
)


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
    NEU = "neu"
    OFFEN = "offen"
    IN_BEARBEITUNG = "in_bearbeitung"          # backward compat
    WARTET_AUF_MANDANT = "wartet_auf_mandant"
    WARTET_INTERN = "wartet_intern"
    INTERN_IN_KLAERUNG = "intern_in_klaerung"
    IN_PRUEFUNG = "in_pruefung"
    BEANTWORTET = "beantwortet"                # backward compat
    GELOEST = "geloest"
    GESCHLOSSEN = "geschlossen"
    ABGEBROCHEN = "abgebrochen"


class TicketPrioritaet(str, enum.Enum):
    NIEDRIG = "niedrig"
    NORMAL = "normal"
    HOCH = "hoch"
    KRITISCH = "kritisch"
    DRINGEND = "dringend"   # backward compat alias


class EskalationStufe(str, enum.Enum):
    REMINDER = "reminder"
    TEAMLEITUNG = "teamleitung"
    LEITUNG = "leitung"


class EmailLogStatus(str, enum.Enum):
    GESENDET = "gesendet"
    ZUGESTELLT = "zugestellt"
    GEBOUNCED = "gebounced"


class FristenRegeltyp(str, enum.Enum):
    FIXES_DATUM = "fixes_datum"
    RELATIV_MONATSENDE = "relativ_monatsende"
    RELATIV_BANKARBEITSTAGE = "relativ_bankarbeitstage"
    RELATIV_ANDERE_FRIST = "relativ_andere_frist"
    EREIGNISBASIERT = "ereignisbasiert"


class SonderaufgabeStatus(str, enum.Enum):
    OFFEN = "offen"
    IN_BEARBEITUNG = "in_bearbeitung"
    ABGESCHLOSSEN = "abgeschlossen"
    ABGEBROCHEN = "abgebrochen"


class MandantKontaktRolle(str, enum.Enum):
    ANSPRECHPARTNER = "ansprechpartner"
    TICKET_KOMMUNIKATION = "ticket_kommunikation"
    UPLOAD_REMINDER = "upload_reminder"


# ─────────────────────────────────────────
# User
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SACHBEARBEITER)
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)        # login disabled, history preserved
    anonymisiert_am = Column(DateTime, nullable=True)    # DSGVO anonymization date
    workload_limit = Column(Float, default=100.0)  # max points per month
    current_workload = Column(Float, default=0.0)  # current assigned points
    total_points_earned = Column(Float, default=0.0)
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
    ticket_kommentare = relationship("TicketKommentar", back_populates="autor", foreign_keys="TicketKommentar.autor_id")
    workflow_items_erledigt = relationship(
        "WorkflowItem",
        back_populates="erledigt_von",
        foreign_keys="WorkflowItem.erledigt_von_id"
    )
    eskalationen = relationship("EskalationLog", back_populates="eskaliert_an", foreign_keys="EskalationLog.eskaliert_an_id")
    dokumente = relationship("Dokument", back_populates="hochgeladen_von")
    audit_logs = relationship("AuditLog", back_populates="benutzer")


# ─────────────────────────────────────────
# Mandant
# ─────────────────────────────────────────

class Mandant(Base):
    __tablename__ = "mandanten"

    id = Column(Integer, primary_key=True, index=True)
    nummer = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    branche = Column(String(100))

    # Ansprechpartner
    ansprechpartner_name = Column(String(255))
    ansprechpartner_email = Column(String(255))
    ansprechpartner_telefon = Column(String(50))

    # Fristen & Organisation
    lohnabschluss_tag = Column(Integer, default=15)  # day of month
    abgabeweg = Column(Enum(Abgabeweg), default=Abgabeweg.EMAIL)
    kategorie = Column(Enum(MandantKategorie), default=MandantKategorie.B)
    service_level = Column(String(50))
    mitarbeiteranzahl = Column(Integer, default=1)
    besonderheiten = Column(Text)

    # Zuordnungen
    sachbearbeiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vertretung_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    portal_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fristenprofil_id = Column(Integer, ForeignKey("fristenprofile.id"), nullable=True)

    # Aufwand / Kalkulation
    stundensatz = Column(Float)
    monatspauschale = Column(Float)

    ist_aktiv = Column(Boolean, default=True)
    onboarding_abgeschlossen = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sachbearbeiter = relationship("User", back_populates="mandanten_als_sachbearbeiter", foreign_keys=[sachbearbeiter_id])
    vertretung = relationship("User", back_populates="mandanten_als_vertretung", foreign_keys=[vertretung_id])
    portal_user = relationship("User", back_populates="mandant_portal", foreign_keys=[portal_user_id])
    workflow_instanzen = relationship("WorkflowInstanz", back_populates="mandant")
    tickets = relationship("Ticket", back_populates="mandant")
    dokumente = relationship("Dokument", back_populates="mandant")
    eskalationen = relationship("EskalationLog", back_populates="mandant")
    email_logs = relationship("EmailLog", back_populates="mandant")
    branchen_liste = relationship("Branche", secondary=mandant_branchen, back_populates="mandanten")
    aenderungen = relationship("MandantAenderung", back_populates="mandant", order_by="MandantAenderung.erstellt_am")
    fristenprofil = relationship("Fristenprofil", foreign_keys=[fristenprofil_id], uselist=False)
    kontakte = relationship("MandantKontakt", back_populates="mandant")
    notizen = relationship("MandantNotiz", back_populates="mandant", order_by="MandantNotiz.version")


# ─────────────────────────────────────────
# Mandant Änderungen (geplante Änderungen)
# ─────────────────────────────────────────

class MandantAenderung(Base):
    __tablename__ = "mandant_aenderungen"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    aenderung_zum = Column(DateTime, nullable=True)  # None = sofort wirksam
    status = Column(String(50), default="geplant")  # geplant, aktiviert, abgebrochen
    aenderungen = Column(Text, nullable=False)  # JSON der geänderten Felder
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktiviert_am = Column(DateTime, nullable=True)
    abgebrochen_am = Column(DateTime, nullable=True)
    abgebrochen_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    mandant = relationship("Mandant", back_populates="aenderungen")
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])
    abgebrochen_von = relationship("User", foreign_keys=[abgebrochen_von_id])


# ─────────────────────────────────────────
# Fristenprofil (client-specific deadline rules)
# ─────────────────────────────────────────

class Fristenprofil(Base):
    __tablename__ = "fristenprofile"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g. "Standard Fristenprofil"
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mandant = relationship("Mandant", backref="fristenprofil_backref", foreign_keys=[mandant_id])
    regeln = relationship("Fristenregel", back_populates="profil", order_by="Fristenregel.position")


class Fristenregel(Base):
    __tablename__ = "fristenregeln"

    id = Column(Integer, primary_key=True, index=True)
    profil_id = Column(Integer, ForeignKey("fristenprofile.id"), nullable=False)
    position = Column(Integer, nullable=False)
    fristart = Column(String(100), nullable=False)  # e.g. "SV-Zahlung", "Lohnsteuer"
    regeltyp = Column(Enum(FristenRegeltyp), nullable=False)
    regel_config = Column(Text, nullable=False)  # JSON config for the rule
    bundesland = Column(String(50), nullable=True)  # for holidays
    interne_vorfrist_tage = Column(Integer, default=0)
    ist_aktiv = Column(Boolean, default=True)

    profil = relationship("Fristenprofil", back_populates="regeln")


# ─────────────────────────────────────────
# Sonderaufgabe (special tasks)
# ─────────────────────────────────────────

class Sonderaufgabe(Base):
    __tablename__ = "sonderaufgaben"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=True)
    monat = Column(Integer, nullable=True)
    jahr = Column(Integer, nullable=True)
    kategorie = Column(String(100), nullable=False)
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    faellig_datum = Column(DateTime, nullable=True)
    status = Column(Enum(SonderaufgabeStatus), default=SonderaufgabeStatus.OFFEN)
    verantwortlicher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    punkte = Column(Float, default=0.0)
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    abgeschlossen_am = Column(DateTime, nullable=True)

    # Relationships
    mandant = relationship("Mandant", backref="sonderaufgaben")
    verantwortlicher = relationship("User", foreign_keys=[verantwortlicher_id])
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])


# ─────────────────────────────────────────
# MandantKontakt (multiple contacts)
# ─────────────────────────────────────────

class MandantKontakt(Base):
    __tablename__ = "mandant_kontakte"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    rolle = Column(Enum(MandantKontaktRolle), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    telefon = Column(String(50), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    mandant = relationship("Mandant", back_populates="kontakte")


# ─────────────────────────────────────────
# MandantNotiz (versioned notes)
# ─────────────────────────────────────────

class MandantNotiz(Base):
    __tablename__ = "mandant_notizen"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    version = Column(Integer, nullable=False)
    inhalt = Column(Text, nullable=False)
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    mandant = relationship("Mandant", back_populates="notizen")
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])


# ─────────────────────────────────────────
# Workflow Template
# ─────────────────────────────────────────

class WorkflowVorlage(Base):
    __tablename__ = "workflow_vorlagen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    branche = Column(String(100))  # optional branche filter
    ist_standard = Column(Boolean, default=False)
    ist_onboarding = Column(Boolean, default=False)
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("WorkflowVorlageItem", back_populates="vorlage", order_by="WorkflowVorlageItem.position")
    instanzen = relationship("WorkflowInstanz", back_populates="vorlage")


class WorkflowVorlageItem(Base):
    __tablename__ = "workflow_vorlage_items"

    id = Column(Integer, primary_key=True, index=True)
    vorlage_id = Column(Integer, ForeignKey("workflow_vorlagen.id"), nullable=False)
    position = Column(Integer, nullable=False)
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    verantwortlich_rolle = Column(Enum(UserRole))
    faellig_offset_tage = Column(Integer, default=0)  # days after month start
    ist_pflicht = Column(Boolean, default=True)
    ist_optional_pro_mandant = Column(Boolean, default=False)  # can be activated per mandant
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)  # 4-eyes
    fristart_referenz = Column(String(100), nullable=True)  # e.g. "SV-Zahlung", links to Fristart
    fristart_offset_tage = Column(Integer, default=0)  # offset from the referenced deadline (negative = before)
    standard_punkte = Column(Float, default=1.0)  # default points for this step

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
    unterlagen_eingegangen_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    unterlagen_faellig = Column(DateTime, nullable=True)
    probe_abrechnung_am = Column(DateTime, nullable=True)
    probe_abrechnung_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    probe_abrechnung_faellig = Column(DateTime, nullable=True)
    probe_geprueft_am = Column(DateTime, nullable=True)
    probe_geprueft_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    probe_geprueft_faellig = Column(DateTime, nullable=True)
    mandant_freigabe_am = Column(DateTime, nullable=True)
    mandant_freigabe_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    mandant_freigabe_faellig = Column(DateTime, nullable=True)
    endabrechnung_am = Column(DateTime, nullable=True)
    endabrechnung_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    endabrechnung_faellig = Column(DateTime, nullable=True)
    versand_am = Column(DateTime, nullable=True)
    versand_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    versand_faellig = Column(DateTime, nullable=True)
    abgeschlossen_am = Column(DateTime, nullable=True)
    abgeschlossen_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    abgeschlossen_faellig = Column(DateTime, nullable=True)
    wiedereroeffnet_am = Column(DateTime, nullable=True)
    wiedereroeffnet_begruendung = Column(Text, nullable=True)

    notizen = Column(Text)
    punkte = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mandant = relationship("Mandant", back_populates="workflow_instanzen")
    vorlage = relationship("WorkflowVorlage", back_populates="instanzen")
    sachbearbeiter = relationship("User", foreign_keys=[sachbearbeiter_id])
    pruefer = relationship("User", foreign_keys=[pruefer_id])
    unterlagen_eingegangen_von = relationship("User", foreign_keys=[unterlagen_eingegangen_von_id])
    probe_abrechnung_von = relationship("User", foreign_keys=[probe_abrechnung_von_id])
    probe_geprueft_von = relationship("User", foreign_keys=[probe_geprueft_von_id])
    mandant_freigabe_von = relationship("User", foreign_keys=[mandant_freigabe_von_id])
    endabrechnung_von = relationship("User", foreign_keys=[endabrechnung_von_id])
    versand_von = relationship("User", foreign_keys=[versand_von_id])
    abgeschlossen_von = relationship("User", foreign_keys=[abgeschlossen_von_id])
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
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    verantwortlich_rolle = Column(Enum(UserRole))
    zugewiesen_an_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    faellig_datum = Column(DateTime, nullable=True)
    ist_pflicht = Column(Boolean, default=True)
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)
    fristart_referenz = Column(String(100), nullable=True)  # links to Fristart for deadline coupling

    status = Column(Enum(ChecklistItemStatus), default=ChecklistItemStatus.OFFEN)
    erledigt_am = Column(DateTime, nullable=True)
    erledigt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notiz = Column(Text)
    punkte = Column(Float, default=0.0)
    ist_blockiert = Column(Boolean, default=False)
    blockiert_grund = Column(String(255), nullable=True)  # e.g. "Wartet auf Ticket #12"

    instanz = relationship("WorkflowInstanz", back_populates="items")
    zugewiesen_an = relationship("User", foreign_keys=[zugewiesen_an_id])
    erledigt_von = relationship("User", back_populates="workflow_items_erledigt", foreign_keys=[erledigt_von_id])
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

    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    status = Column(Enum(TicketStatus), default=TicketStatus.NEU)
    prioritaet = Column(Enum(TicketPrioritaet), default=TicketPrioritaet.NORMAL)
    kategorie = Column(String(100))
    unterkategorie = Column(String(100), nullable=True)

    # Month reference (which payroll month this ticket belongs to)
    monat = Column(Integer, nullable=True)
    jahr = Column(Integer, nullable=True)

    # SLA & Escalation
    faellig_bis = Column(DateTime, nullable=True)
    eskalationsstufe = Column(Enum(EskalationStufe), nullable=True)
    wiedervorlage_datum = Column(DateTime, nullable=True)

    # Abbruch
    abbruch_grund = Column(Text, nullable=True)

    # Workflow-Item linking (optional)
    workflow_item_id = Column(Integer, ForeignKey("workflow_items.id"), nullable=True)

    geschlossen_am = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mandant = relationship("Mandant", back_populates="tickets")
    workflow_instanz = relationship("WorkflowInstanz", back_populates="tickets")
    workflow_item = relationship("WorkflowItem", foreign_keys=[workflow_item_id])
    erstellt_von = relationship("User", back_populates="tickets_erstellt", foreign_keys=[erstellt_von_id])
    zugewiesen_an = relationship("User", foreign_keys=[zugewiesen_an_id])
    kommentare = relationship("TicketKommentar", back_populates="ticket", order_by="TicketKommentar.created_at")
    anhaenge = relationship("TicketAnhang", back_populates="ticket", order_by="TicketAnhang.created_at")


class TicketKommentar(Base):
    __tablename__ = "ticket_kommentare"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    autor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    inhalt = Column(Text, nullable=False)
    ist_intern = Column(Boolean, default=False, nullable=False)  # internal-only, not visible to client
    zitat_id = Column(Integer, ForeignKey("ticket_kommentare.id"), nullable=True)  # quote/reply
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="kommentare")
    autor = relationship("User", back_populates="ticket_kommentare")
    zitat = relationship("TicketKommentar", remote_side="TicketKommentar.id", foreign_keys=[zitat_id])
    anhaenge = relationship("TicketAnhang", back_populates="kommentar", order_by="TicketAnhang.created_at")


# ─────────────────────────────────────────
# SLA Konfiguration
# ─────────────────────────────────────────

class SLAKonfiguration(Base):
    __tablename__ = "sla_konfigurationen"

    id = Column(Integer, primary_key=True, index=True)
    kategorie = Column(String(100), nullable=False)          # ticket category name
    prioritaet = Column(Enum(TicketPrioritaet), nullable=True)  # null = applies to all prios
    sla_stunden = Column(Integer, nullable=False, default=48)   # hours until SLA breach
    eskalation_stufe1_stunden = Column(Integer, default=72)     # hours until level-1 escalation
    eskalation_stufe2_stunden = Column(Integer, default=96)     # hours until level-2 escalation
    created_at = Column(DateTime, default=datetime.utcnow)


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

    name = Column(String(255), nullable=False)
    dateityp = Column(String(50))
    dateigroesse = Column(Integer)  # bytes
    speicherort = Column(String(500))    # path or URL
    kategorie = Column(String(100))
    notiz = Column(Text)
    ist_geloescht = Column(Boolean, default=False)  # logical delete only
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


# ─────────────────────────────────────────
# Audit Log (append-only, manipulation-protected)
# ─────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    objekt_typ = Column(String(100), nullable=False)      # e.g. "mandant", "ticket", "workflow"
    objekt_id = Column(Integer, nullable=True)
    mandant_id = Column(Integer, nullable=True)       # denormalized for fast filtering
    monat = Column(Integer, nullable=True)
    jahr = Column(Integer, nullable=True)
    aktionstyp = Column(String(100), nullable=False)       # e.g. "erstellt", "statusaenderung"
    alter_wert = Column(Text, nullable=True)          # JSON string
    neuer_wert = Column(Text, nullable=True)          # JSON string
    benutzer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    benutzerrolle = Column(String(50), nullable=True)
    zeitstempel = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_adresse = Column(String(45), nullable=True)
    beschreibung = Column(Text, nullable=True)        # human-readable summary

    benutzer = relationship("User", back_populates="audit_logs")


# ─────────────────────────────────────────
# Email Templates & Log
# ─────────────────────────────────────────

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    betreff = Column(String(255), nullable=False)
    html_inhalt = Column(Text, nullable=False)
    text_inhalt = Column(Text, nullable=True)
    beschreibung = Column(Text, nullable=True)
    typ = Column(String(100), nullable=True)              # "onboarding_welcome", "onboarding_reminder", "unterlagen_reminder"
    ist_aktiv = Column(Boolean, default=True)
    reihenfolge = Column(Integer, default=0)         # for onboarding sequence ordering
    verzoegerung_tage = Column(Integer, default=0)   # days after previous email in sequence
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = relationship("EmailLog", back_populates="template")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    empfaenger = Column(String(255), nullable=False)
    betreff = Column(String(255), nullable=False)
    status = Column(Enum(EmailLogStatus), default=EmailLogStatus.GESENDET)
    gesendet_am = Column(DateTime, default=datetime.utcnow)
    fehler = Column(Text, nullable=True)

    template = relationship("EmailTemplate", back_populates="logs")
    mandant = relationship("Mandant", back_populates="email_logs")


# ─────────────────────────────────────────
# Branche (Admin Stammdaten)
# ─────────────────────────────────────────

class Branche(Base):
    __tablename__ = "branchen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    beschreibung = Column(Text, nullable=True)
    faktor = Column(Float, default=1.0)               # Punkte-/Komplexitätsfaktor
    soka_relevant = Column(Boolean, default=False)     # SOKA-Relevanz
    tags = Column(Text, nullable=True)                 # JSON-encoded list of tags
    ist_archiviert = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mandanten = relationship("Mandant", secondary=mandant_branchen, back_populates="branchen_liste")


# ─────────────────────────────────────────
# Ausgabeweg (Admin Stammdaten)
# ─────────────────────────────────────────

class AusgabewegConfig(Base):
    __tablename__ = "ausgabeweg_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    beschreibung = Column(Text, nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    beeinflusst_workflow = Column(Boolean, default=False)  # adds extra workflow steps
    zusatz_workflow_schritt = Column(String(255), nullable=True)  # e.g. "Upload ins Portal"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# Ticket-Anhänge
# ─────────────────────────────────────────

class TicketAnhang(Base):
    __tablename__ = "ticket_anhaenge"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    kommentar_id = Column(Integer, ForeignKey("ticket_kommentare.id"), nullable=True)
    dateiname = Column(String(255), nullable=False)
    dateityp = Column(String(50), nullable=True)
    dateigroesse = Column(Integer, nullable=True)        # bytes
    speicherort = Column(String(500), nullable=False)
    hash = Column(String(128), nullable=True)                 # file hash for integrity
    hochgeladen_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ist_intern = Column(Boolean, default=False)          # internal-only, not visible to mandant
    ist_geloescht = Column(Boolean, default=False)       # logical delete
    loeschung_begruendung = Column(Text, nullable=True)
    geloescht_am = Column(DateTime, nullable=True)
    geloescht_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="anhaenge")
    kommentar = relationship("TicketKommentar", back_populates="anhaenge")
    hochgeladen_von = relationship("User", foreign_keys=[hochgeladen_von_id])
    geloescht_von = relationship("User", foreign_keys=[geloescht_von_id])


# ─────────────────────────────────────────
# SMTP-Konfiguration (Admin Mail)
# ─────────────────────────────────────────

class SmtpKonfiguration(Base):
    __tablename__ = "smtp_konfigurationen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Standard")
    server = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=587)
    tls_ssl = Column(String(20), default="starttls")       # "starttls", "ssl", "none"
    auth_user = Column(String(255), nullable=True)
    auth_password_encrypted = Column(String(500), nullable=True)
    absender_email = Column(String(255), nullable=False)
    reply_to = Column(String(255), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# IMAP-Konfiguration (Admin Mail)
# ─────────────────────────────────────────

class ImapKonfiguration(Base):
    __tablename__ = "imap_konfigurationen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Standard")
    server = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=993)
    tls_ssl = Column(String(20), default="ssl")            # "ssl", "starttls", "none"
    auth_user = Column(String(255), nullable=True)
    auth_password_encrypted = Column(String(500), nullable=True)
    postfach = Column(String(255), default="INBOX")
    ordner = Column(String(255), nullable=True)              # e.g. "INBOX/Tickets"
    polling_intervall_sekunden = Column(Integer, default=300)
    zuordnung_methode = Column(String(50), default="betreff")  # "betreff", "message_id", "reply_to_token"
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# System-Defaults (Admin)
# ─────────────────────────────────────────

class SystemDefault(Base):
    __tablename__ = "system_defaults"

    id = Column(Integer, primary_key=True, index=True)
    bereich = Column(String(100), nullable=False)            # e.g. "branchen", "ausgabewege", "fristen", etc.
    name = Column(String(255), nullable=False)
    konfiguration = Column(Text, nullable=True)          # JSON config
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# Upload-Konfiguration (Anhänge)
# ─────────────────────────────────────────

class UploadKonfiguration(Base):
    __tablename__ = "upload_konfigurationen"

    id = Column(Integer, primary_key=True, index=True)
    max_dateigroesse_mb = Column(Integer, default=10)
    erlaubte_dateitypen = Column(Text, default='["pdf","doc","docx","xls","xlsx","csv","jpg","jpeg","png","txt","zip"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# Fristen-Vorlagen (Default Deadline Templates)
# ─────────────────────────────────────────

class FristenVorlage(Base):
    """Default deadline type templates (DE). Can be activated per mandant."""
    __tablename__ = "fristen_vorlagen"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)          # e.g. "SV_ZAHLUNG"
    name = Column(String(255), nullable=False)                       # e.g. "SV-Beitragszahlung"
    beschreibung = Column(Text, nullable=True)
    regeltyp = Column(Enum(FristenRegeltyp), nullable=False)
    regel_config = Column(Text, nullable=False)                 # JSON config
    default_interne_vorfrist_tage = Column(Integer, default=2)
    ist_jahresbezogen = Column(Boolean, default=False)          # e.g. DEÜV Jahresmeldung, UV
    ist_ereignisbasiert = Column(Boolean, default=False)        # e.g. DEÜV Sofortmeldung
    branchenfilter = Column(String(100), nullable=True)              # null = all, "SOKA" = only SOKA-relevant
    anmeldezeitraum = Column(String(50), nullable=True)             # "monatlich", "vierteljaehrlich", "jaehrlich"
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# WorkflowSchrittTyp (Admin-definable workflow step types)
# ─────────────────────────────────────────

class WorkflowSchrittTyp(Base):
    """Admin-definable workflow step types per Section 8."""
    __tablename__ = "workflow_schritt_typen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    beschreibung = Column(Text, nullable=True)
    ist_pflicht = Column(Boolean, default=True)
    standard_rolle = Column(Enum(UserRole), nullable=True)      # default role
    abhaengigkeit_von = Column(String(255), nullable=True)           # name of blocking step type
    fristart_referenz = Column(String(100), nullable=True)           # e.g. "SV_ZAHLUNG"
    fristart_offset_tage = Column(Integer, default=0)           # offset from deadline
    standard_punkte = Column(Float, default=1.0)
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# Mandant-specific Workflow Step Activation
# ─────────────────────────────────────────

class MandantWorkflowSchritt(Base):
    """Activates optional workflow step types for a specific mandant."""
    __tablename__ = "mandant_workflow_schritte"

    id = Column(Integer, primary_key=True, index=True)
    mandant_id = Column(Integer, ForeignKey("mandanten.id"), nullable=False)
    schritt_typ_id = Column(Integer, ForeignKey("workflow_schritt_typen.id"), nullable=False)
    ist_aktiv = Column(Boolean, default=True)
    aenderung_zum = Column(DateTime, nullable=True)     # effective date
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    mandant = relationship("Mandant", backref="workflow_schritte")
    schritt_typ = relationship("WorkflowSchrittTyp")
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])


# ─────────────────────────────────────────
# Punkte-Konfiguration (Workload Point Rules)
# ─────────────────────────────────────────

class PunkteKonfiguration(Base):
    """Admin-configurable point calculation rules per Section 4.4."""
    __tablename__ = "punkte_konfigurationen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)                       # e.g. "Standard", "SOKA"
    kategorie_basis = Column(Text, nullable=False)              # JSON: {"A": 10, "B": 5, "C": 3}
    mitarbeiter_stufen = Column(Text, nullable=False)           # JSON: [{"bis": 10, "faktor": 1.0}, {"bis": 50, "faktor": 1.5}]
    branchen_faktoren = Column(Text, nullable=True)             # JSON: {"Baugewerbe": 1.3}
    zusatzmodul_punkte = Column(Text, nullable=True)            # JSON: {"viele_eintritte": 2, "einmalzahlungen": 1}
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
