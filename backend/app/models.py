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
    INTERN_IN_KLAERUNG = "intern_in_klaerung"
    BEANTWORTET = "beantwortet"                # backward compat
    GELOEST = "geloest"
    GESCHLOSSEN = "geschlossen"


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
    wiedereroeffnet_am = Column(DateTime, nullable=True)
    wiedereroeffnet_begruendung = Column(Text, nullable=True)

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
    status = Column(Enum(TicketStatus), default=TicketStatus.NEU)
    prioritaet = Column(Enum(TicketPrioritaet), default=TicketPrioritaet.NORMAL)
    kategorie = Column(String)

    # Month reference (which payroll month this ticket belongs to)
    monat = Column(Integer, nullable=True)
    jahr = Column(Integer, nullable=True)

    # SLA & Escalation
    faellig_bis = Column(DateTime, nullable=True)
    eskalationsstufe = Column(Enum(EskalationStufe), nullable=True)

    geschlossen_am = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mandant = relationship("Mandant", back_populates="tickets")
    workflow_instanz = relationship("WorkflowInstanz", back_populates="tickets")
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
    kategorie = Column(String, nullable=False)          # ticket category name
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

    name = Column(String, nullable=False)
    dateityp = Column(String)
    dateigroesse = Column(Integer)  # bytes
    speicherort = Column(String)    # path or URL
    kategorie = Column(String)
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
    objekt_typ = Column(String, nullable=False)      # e.g. "mandant", "ticket", "workflow"
    objekt_id = Column(Integer, nullable=True)
    mandant_id = Column(Integer, nullable=True)       # denormalized for fast filtering
    monat = Column(Integer, nullable=True)
    jahr = Column(Integer, nullable=True)
    aktionstyp = Column(String, nullable=False)       # e.g. "erstellt", "statusaenderung"
    alter_wert = Column(Text, nullable=True)          # JSON string
    neuer_wert = Column(Text, nullable=True)          # JSON string
    benutzer_id = Column(Integer, nullable=True)
    benutzerrolle = Column(String, nullable=True)
    zeitstempel = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_adresse = Column(String, nullable=True)
    beschreibung = Column(Text, nullable=True)        # human-readable summary


# ─────────────────────────────────────────
# Email Templates & Log
# ─────────────────────────────────────────

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    betreff = Column(String, nullable=False)
    html_inhalt = Column(Text, nullable=False)
    text_inhalt = Column(Text, nullable=True)
    beschreibung = Column(Text, nullable=True)
    typ = Column(String, nullable=True)              # "onboarding_welcome", "onboarding_reminder", "unterlagen_reminder"
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
    empfaenger = Column(String, nullable=False)
    betreff = Column(String, nullable=False)
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
    name = Column(String, nullable=False, unique=True)
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
    name = Column(String, nullable=False, unique=True)
    beschreibung = Column(Text, nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    beeinflusst_workflow = Column(Boolean, default=False)  # adds extra workflow steps
    zusatz_workflow_schritt = Column(String, nullable=True)  # e.g. "Upload ins Portal"
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
    dateiname = Column(String, nullable=False)
    dateityp = Column(String, nullable=True)
    dateigroesse = Column(Integer, nullable=True)        # bytes
    speicherort = Column(String, nullable=False)
    hash = Column(String, nullable=True)                 # file hash for integrity
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
    name = Column(String, nullable=False, default="Standard")
    server = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=587)
    tls_ssl = Column(String, default="starttls")       # "starttls", "ssl", "none"
    auth_user = Column(String, nullable=True)
    auth_password_encrypted = Column(String, nullable=True)
    absender_email = Column(String, nullable=False)
    reply_to = Column(String, nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# IMAP-Konfiguration (Admin Mail)
# ─────────────────────────────────────────

class ImapKonfiguration(Base):
    __tablename__ = "imap_konfigurationen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Standard")
    server = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=993)
    tls_ssl = Column(String, default="ssl")            # "ssl", "starttls", "none"
    auth_user = Column(String, nullable=True)
    auth_password_encrypted = Column(String, nullable=True)
    postfach = Column(String, default="INBOX")
    ordner = Column(String, nullable=True)              # e.g. "INBOX/Tickets"
    polling_intervall_sekunden = Column(Integer, default=300)
    zuordnung_methode = Column(String, default="betreff")  # "betreff", "message_id", "reply_to_token"
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# System-Defaults (Admin)
# ─────────────────────────────────────────

class SystemDefault(Base):
    __tablename__ = "system_defaults"

    id = Column(Integer, primary_key=True, index=True)
    bereich = Column(String, nullable=False)            # e.g. "branchen", "ausgabewege", "fristen", etc.
    name = Column(String, nullable=False)
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
