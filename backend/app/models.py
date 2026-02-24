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

# Association table für globale Events zu Workflow-Instanzen
workflow_instanz_global_events = Table(
    "workflow_instanz_global_events",
    Base.metadata,
    Column("workflow_instanz_id", Integer, ForeignKey("workflow_instanzen.id"), primary_key=True),
    Column("global_event_id", Integer, ForeignKey("global_events.id"), primary_key=True),
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


class BrancheTyp(str, enum.Enum):
    INDUSTRIE = "industrie"
    HANDEL = "handel"
    HANDWERK = "handwerk"
    FREIBERUFLER = "freiberufler"
    GESUNDHEIT = "gesundheit"
    DIENSTLEISTUNGEN = "dienstleistungen"
    BAUWIRTSCHAFT = "bauwirtschaft"
    LANDWIRTSCHAFT = "landwirtschaft"
    SONSTIGE = "sonstige"


class WorkflowSchrittTyp(str, enum.Enum):
    DATENERFASSUNG = "datenerfassung"
    PRUEFER_PFLICHT = "pruefer_pflicht"  # requires 4-eyes
    ABSCHLUSSFRIST = "abschlussfrist"  # links to external deadline
    UPLOAD = "upload"  # requires document
    GENEHMIGUNG = "genehmigung"  # approval step
    BERECHNUNG = "berechnung"  # calculation step
    VERSAND = "versand"  # delivery step
    VERARBEITUNG = "verarbeitung"  # generic processing


class AmpelRegelTyp(str, enum.Enum):
    UEBERFAELLIG = "ueberfaellig"  # days overdue = red
    WARNUNG = "warnung"  # days until deadline = yellow
    KRITISCHES_TICKET = "kritisches_ticket"  # critical tickets = red
    BLOCKIERT = "blockiert"  # blocked by dependency


class GlobalEventTyp(str, enum.Enum):
    JAHRESWECHSEL = "jahreswechsel"
    MINDESTLOHN_ERHOEHUNG = "mindestlohn_erhoehung"
    GESETZESAENDERUNG = "gesetzesaenderung"
    SV_WERTE_AENDERUNG = "sv_werte_aenderung"
    STEUERAENDERUNG = "steueraenderung"
    KURZARBEIT = "kurzarbeit"
    CORONA_MASSNAHME = "corona_massnahme"
    SONSTIG = "sonstig"


class WorkflowSchrittEbene(str, enum.Enum):
    STANDARD = "standard"           # Teil des Standard-Workflows
    BRANCHE = "branche"             # Branchenspezifisch
    MANDANT = "mandant"             # Mandantenspezifisch
    GLOBAL_EVENT = "global_event"   # Globales Event (z.B. Jahreswechsel)


class WorkflowItemStatus(str, enum.Enum):
    """Detaillierter Status für Workflow-Items mit Phasen."""
    OFFEN = "offen"                          # Bereit zur Bearbeitung
    BLOCKIERT = "blockiert"                  # Wartet auf andere Items
    IN_BEARBEITUNG = "in_bearbeitung"        # Aktiv bearbeitet
    FERTIG = "fertig"                        # Abgeschlossen + System updated
    IN_BEARBEITUNG_BLOCKIERT = "in_bearbeitung_blockiert"  # Hybrid: teils blockiert, teils gemacht
    UEBERSPRUNGEN = "uebersprungen"          # Bewusst übersprungen (optional)


class WorkflowItemDependencyTyp(str, enum.Enum):
    """Typ der Abhängigkeit zwischen Items."""
    BLOCKIERT_VON = "blockiert_von"          # Target ist blockiert bis Source fertig
    MUSS_VOR = "muss_vor"                    # Source muss vor Target erledigt sein (historisch)
    PARALLEL_OK = "parallel_ok"              # Können parallel laufen (aber sequenziell aufgelistet)
    OPTIONAL_NACH = "optional_nach"          # Target optional, aber sollte nach Source kommen


class StichtabCategory(str, enum.Enum):
    """Kategorien für Stichtage zur besseren Verwaltung."""
    ZAHLSTAG = "zahlstag"                    # Lohnzahltag, Steuerzahlung, SV-Zahlung
    MELDUNG = "meldung"                      # Meldepflicht (DEÜV, Statistik, etc.)
    INTERN = "intern"                        # Interne Deadline (Prüfung, Freigabe)
    VORBEREITUNG = "vorbereitung"           # Vorbereitung auf externen Stichtag


# ─────────────────────────────────────────
# Tenant (Multi-Tenancy-Unterstützung)
# ─────────────────────────────────────────

class Tenant(Base):
    """
    Multi-Tenant-Unterstützung: Ein Tenant repräsentiert eine Organisation/Kanzlei,
    die mehrere Abrechnungsfirmen haben kann.
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)  # Kurzcode für URLs etc.
    beschreibung = Column(Text, nullable=True)
    
    # Konfiguration (JSON)
    # { "features": ["multi_abrechnungsfirma"], "max_mandanten": 1000, ... }
    konfiguration = Column(Text, nullable=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primaerfarbe = Column(String(7), nullable=True)  # Hex-Farbe, z.B. "#003366"
    
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    abrechnungsfirmen = relationship("Abrechnungsfirma", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant")


class Abrechnungsfirma(Base):
    """
    Eine Abrechnungsfirma innerhalb eines Tenants.
    Mandanten werden einer Abrechnungsfirma zugeordnet.
    """
    __tablename__ = "abrechnungsfirmen"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)  # Kurzcode innerhalb des Tenants
    beschreibung = Column(Text, nullable=True)
    
    # Adressdaten
    strasse = Column(String(255), nullable=True)
    plz = Column(String(10), nullable=True)
    ort = Column(String(100), nullable=True)
    land = Column(String(100), default="Deutschland")
    
    # Kontaktdaten
    telefon = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Steuerliche Daten
    steuernummer = Column(String(50), nullable=True)
    ustid = Column(String(50), nullable=True)
    
    # Bankverbindung
    bank_name = Column(String(255), nullable=True)
    iban = Column(String(34), nullable=True)
    bic = Column(String(11), nullable=True)
    
    # Spezielle Workflow-Konfiguration für diese Firma
    # JSON: { "standard_vorlage_id": 1, "default_sla_tage": 10 }
    workflow_konfiguration = Column(Text, nullable=True)
    
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="abrechnungsfirmen")
    mandanten = relationship("Mandant", back_populates="abrechnungsfirma")


# ─────────────────────────────────────────
# User
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)  # Multi-Tenant
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
    tenant = relationship("Tenant", back_populates="users")
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
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)  # Multi-Tenant
    abrechnungsfirma_id = Column(Integer, ForeignKey("abrechnungsfirmen.id"), nullable=True)
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

    # Workflow-Konfiguration: optionale Vorlagen-Items pro Mandant
    # JSON: { "vorlage_item_ids": [1, 2, 3] } - IDs der optionalen Items die aktiviert werden sollen
    workflow_konfiguration = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    abrechnungsfirma = relationship("Abrechnungsfirma", back_populates="mandanten", foreign_keys=[abrechnungsfirma_id])
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
# Branche Profile (branch-specific configurations)
# ─────────────────────────────────────────

class Branche(Base):
    __tablename__ = "branchen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    typ = Column(Enum(BrancheTyp), nullable=False)
    beschreibung = Column(Text)
    
    # Standard deadline for payroll submission day of month
    # E.g., industry: 10th, trade: 15th
    lohnabschluss_standardtag = Column(Integer, default=10)
    
    # SLA warning threshold (days before deadline)
    sla_warnung_tage = Column(Integer, default=2)
    
    # Configuration for this branch (JSON)
    # { "requiresAuditTrail": true, "requiresSignature": false, ... }
    konfiguration = Column(Text, nullable=True)
    
    # Admin Stammdaten fields
    faktor = Column(Float, default=1.0)               # Punkte-/Komplexitätsfaktor
    soka_relevant = Column(Boolean, default=False)     # SOKA-Relevanz
    tags = Column(Text, nullable=True)                 # JSON-encoded list of tags
    
    ist_aktiv = Column(Boolean, default=True)
    ist_archiviert = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    mandanten = relationship("Mandant", secondary=mandant_branchen, back_populates="branchen_liste")
    workflow_vorlagen = relationship("WorkflowVorlage", back_populates="branche")
    fristenprofile = relationship("BrancheFristenprofil", back_populates="branche")


class BrancheFristenprofil(Base):
    """Branch-specific deadline profile with variability rules."""
    __tablename__ = "branche_fristenprofile"

    id = Column(Integer, primary_key=True, index=True)
    branche_id = Column(Integer, ForeignKey("branchen.id"), nullable=False)
    name = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    ist_standard = Column(Boolean, default=False)
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    branche = relationship("Branche", back_populates="fristenprofile")
    fristen = relationship("BrancheFrist", back_populates="profil", order_by="BrancheFrist.position")


class BrancheFrist(Base):
    """Specific deadline (Frist) for a branch profile."""
    __tablename__ = "branche_fristen"

    id = Column(Integer, primary_key=True, index=True)
    profil_id = Column(Integer, ForeignKey("branche_fristenprofile.id"), nullable=False)
    position = Column(Integer, nullable=False)
    
    # E.g., "SV-Meldung", "Lohnsteuer-Zahlung", "Abrechnungsunterlagen"
    bezeichnung = Column(String(255), nullable=False)
    
    # Rule type for calculation
    regeltyp = Column(Enum(FristenRegeltyp), nullable=False)
    
    # JSON config specific to rule type
    # FIXES_DATUM: { "tag": 15, "monat": 1 }
    # RELATIV_MONATSENDE: { "tage_nach_monatsende": -5 }
    # RELATIV_BANKARBEITSTAGE: { "bankarbeitstage_nach_zahlungsgruppe3": 1 }
    regelkonfiguration = Column(Text, nullable=False)
    
    # Optional: internal advance notice (tage vor Deadline
    interne_vorfrist_tage = Column(Integer, default=0)
    
    # Which workflow items should use this deadline?
    # JSON: ["workflow_vorlage_item_id_1", "workflow_vorlage_item_id_2"]
    zugeordnete_items = Column(Text, nullable=True)
    
    ist_aktiv = Column(Boolean, default=True)
    
    profil = relationship("BrancheFristenprofil", back_populates="fristen")


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
    branche_typ = Column(Enum(BrancheTyp), nullable=True)  # target branch type
    branche_id = Column(Integer, ForeignKey("branchen.id"), nullable=True)  # specific branch
    ist_standard = Column(Boolean, default=False)
    ist_onboarding = Column(Boolean, default=False)
    kategorie = Column(Enum(MandantKategorie), nullable=True)  # A/B/C - filter by complexity
    
    # SLA configuration for this workflow
    # JSON: { "gesamtdauer_tage": 30, "warnung_tage": 5 }
    sla_konfiguration = Column(Text, nullable=True)
    
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_archiviert = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    branche = relationship("Branche", back_populates="workflow_vorlagen", foreign_keys=[branche_id])
    items = relationship("WorkflowVorlageItem", back_populates="vorlage", order_by="WorkflowVorlageItem.position", cascade="all, delete-orphan")
    phasen = relationship("WorkflowPhase", back_populates="vorlage", order_by="WorkflowPhase.position", cascade="all, delete-orphan")
    item_dependencies = relationship("WorkflowVorlageItemDependency", back_populates="vorlage", cascade="all, delete-orphan")
    instanzen = relationship("WorkflowInstanz", back_populates="vorlage")


class WorkflowPhase(Base):
    """Phasen im Workflow - strukturiert den Ablauf in logische Abschnitte."""
    __tablename__ = "workflow_phasen"
    
    id = Column(Integer, primary_key=True, index=True)
    vorlage_id = Column(Integer, ForeignKey("workflow_vorlagen.id"), nullable=False)
    position = Column(Integer, nullable=False)  # 1=Dateneingang, 2=Prüfung, etc.
    name = Column(String(255), nullable=False)  # z.B. "Dateneingang"
    beschreibung = Column(Text, nullable=True)
    
    # Icon/Category für Frontend
    icon = Column(String(50), nullable=True)  # z.B. "inbox", "check", "send"
    
    # Standardtermine (Tag des Monats, z.B. "5" = 5. des Monats)
    # Kann pro Branche overridden werden
    standard_frist_tag = Column(Integer, nullable=True)  # 1-31, None = flexibel
    
    # Ist das eine Kernprozess-Phase? (zentraler Fortschritt)
    ist_kernprozess = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vorlage = relationship("WorkflowVorlage", back_populates="phasen")
    items = relationship("WorkflowVorlageItem", back_populates="phase")


class WorkflowVorlageItem(Base):
    __tablename__ = "workflow_vorlage_items"

    id = Column(Integer, primary_key=True, index=True)
    vorlage_id = Column(Integer, ForeignKey("workflow_vorlagen.id"), nullable=False)
    phase_id = Column(Integer, ForeignKey("workflow_phasen.id"), nullable=True)  # NEW: Phase Link
    position = Column(Integer, nullable=False)
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    schritttyp = Column(Enum(WorkflowSchrittTyp), default=WorkflowSchrittTyp.VERARBEITUNG)
    
    # Assignment & Responsibility
    verantwortlich_rolle = Column(Enum(UserRole))  # if None, free assignment
    
    # Deadline configuration
    faellig_offset_tage = Column(Integer, default=0)  # days after month start
    ist_pflicht = Column(Boolean, default=True)
    ist_optional_pro_mandant = Column(Boolean, default=False)  # can be activated per mandant
    
    # Dokumentation & Prüfung
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)  # 4-eyes
    
    # Fristen integration
    fristart_referenz = Column(String(100), nullable=True)  # e.g. "SV-Zahlung", links to BrancheFrist
    fristart_offset_tage = Column(Integer, default=0)  # offset from the referenced deadline (negative = before)
    
    # Dependency management
    # JSON: ["item_id_1", "item_id_2"] - must be completed before this step
    abhaengig_von_items = Column(Text, nullable=True)
    
    # Points system
    standard_punkte = Column(Float, default=1.0)
    
    # Blocking rules
    # JSON: { "kritisches_ticket_bricht": true, "blockt_abschluss": true }
    blockier_konfiguration = Column(Text, nullable=True)

    # Prozessdesigner: visual canvas position
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)

    vorlage = relationship("WorkflowVorlage", back_populates="items")
    phase = relationship("WorkflowPhase", back_populates="items")
    dependencies_from = relationship("WorkflowVorlageItemDependency", foreign_keys="WorkflowVorlageItemDependency.source_item_id", back_populates="source_item")
    dependencies_to = relationship("WorkflowVorlageItemDependency", foreign_keys="WorkflowVorlageItemDependency.target_item_id", back_populates="target_item")
    checklisten = relationship("ProzessSchrittChecklistItem", back_populates="vorlage_item", cascade="all, delete-orphan", order_by="ProzessSchrittChecklistItem.position")


class WorkflowVorlageItemDependency(Base):
    """Abhängigkeiten zwischen Items einer Vorlage (definierten Blockierungsregeln)."""
    __tablename__ = "workflow_vorlage_item_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    vorlage_id = Column(Integer, ForeignKey("workflow_vorlagen.id"), nullable=False)
    source_item_id = Column(Integer, ForeignKey("workflow_vorlage_items.id"), nullable=False)  # Item das fertig sein muss
    target_item_id = Column(Integer, ForeignKey("workflow_vorlage_items.id"), nullable=False)  # Item das blockiert ist
    
    # Typ der Abhängigkeit
    typ = Column(Enum(WorkflowItemDependencyTyp), default=WorkflowItemDependencyTyp.BLOCKIERT_VON)
    
    # Optionale Beschreibung
    beschreibung = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vorlage = relationship("WorkflowVorlage", back_populates="item_dependencies")
    source_item = relationship("WorkflowVorlageItem", foreign_keys=[source_item_id], back_populates="dependencies_from")
    target_item = relationship("WorkflowVorlageItem", foreign_keys=[target_item_id], back_populates="dependencies_to")


# ─────────────────────────────────────────
# Prozessdesigner: Checklist items per step
# ─────────────────────────────────────────

class ProzessSchrittChecklistItem(Base):
    """
    Checklisten-Einträge für einen einzelnen Prozessschritt (WorkflowVorlageItem).
    Werden monatlich beim Abarbeiten des Schritts durchgegangen.
    """
    __tablename__ = "prozess_schritt_checklisten"

    id = Column(Integer, primary_key=True, index=True)
    vorlage_item_id = Column(Integer, ForeignKey("workflow_vorlage_items.id"), nullable=False)
    position = Column(Integer, nullable=False, default=1)
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text, nullable=True)
    ist_pflicht = Column(Boolean, default=True)
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vorlage_item = relationship("WorkflowVorlageItem", back_populates="checklisten")


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
    
    # Workflow status & visibility
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.OFFEN)
    ampelstatus = Column(Enum(Ampelstatus), default=Ampelstatus.GRUEN)
    last_ampel_update = Column(DateTime, nullable=True)

    # Team assignments
    sachbearbeiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pruefer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # SLA & Deadline tracking
    sla_deadline = Column(DateTime, nullable=True)  # calculated from branche + fristen
    sla_status = Column(String(50), default="gruen")  # gruen/gelb/rot
    
    # Timestamps for key process steps (backward compat)
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
    
    # Re-open tracking
    wiedereroeffnet_am = Column(DateTime, nullable=True)
    wiedereroeffnet_begruendung = Column(Text, nullable=True)

    # Notes & metadata
    notizen = Column(Text)
    punkte = Column(Float, default=0.0)
    
    # Time tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # when actually started
    durchlaufzeit_stunden = Column(Float, nullable=True)  # calculated after completion
    
    # Estimated vs actual
    geschaetzte_dauer_tage = Column(Integer, nullable=True)  # estimated from SLA config
    verzoegerung_tage = Column(Integer, nullable=True)  # delay after SLA deadline
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
    global_events = relationship("GlobalEvent", secondary=workflow_instanz_global_events, back_populates="workflow_instanzen")


class WorkflowItem(Base):
    __tablename__ = "workflow_items"

    id = Column(Integer, primary_key=True, index=True)
    instanz_id = Column(Integer, ForeignKey("workflow_instanzen.id"), nullable=False)
    vorlage_item_id = Column(Integer, ForeignKey("workflow_vorlage_items.id"), nullable=True)
    phase_id = Column(Integer, ForeignKey("workflow_phasen.id"), nullable=True)  # NEW: Link zur Phase
    position = Column(Integer, nullable=False)
    
    # Task details
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text)
    schritttyp = Column(Enum(WorkflowSchrittTyp), default=WorkflowSchrittTyp.VERARBEITUNG)
    
    # Assignment
    verantwortlich_rolle = Column(Enum(UserRole))
    zugewiesen_an_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Deadline & SLA
    faellig_datum = Column(DateTime, nullable=True)
    sla_warnung_ab = Column(DateTime, nullable=True)  # warning deadline (e.g., 2 days before due)
    
    # Attributes
    ist_pflicht = Column(Boolean, default=True)
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)  # 4-eyes principle
    fristart_referenz = Column(String(100), nullable=True)  # links to deadline rule

    # Status & completion - NEW: erweitert für Phase-System
    status = Column(Enum(WorkflowItemStatus), default=WorkflowItemStatus.OFFEN)
    erledigt_am = Column(DateTime, nullable=True)
    erledigt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)  # when work actually started
    actual_duration_minuten = Column(Integer, nullable=True)  # actual time spent
    
    # Blocking management - NEW: Liste von blockierenden Item-IDs
    blockiert_von_item_ids = Column(Text, nullable=True)  # JSON: [item_id, ...]
    blockiert_grund = Column(String(255), nullable=True)  # e.g. "Wartet auf Item #12"
    blockierung_seit = Column(DateTime, nullable=True)
    
    # Dependencies
    # JSON: ["item_id_1", "item_id_2"] - parent items that must be done first
    abhaengig_von_items = Column(Text, nullable=True)
    
    # Metadata
    notiz = Column(Text)
    punkte = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Ampel-relevant
    ist_ueberfaellig = Column(Boolean, default=False)
    last_ampel_check = Column(DateTime, nullable=True)

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
# WorkflowSchrittTypConfig (Admin-definable workflow step types)
# ─────────────────────────────────────────

class WorkflowSchrittTypConfig(Base):
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
    schritt_typ = relationship("WorkflowSchrittTypConfig")
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


# ─────────────────────────────────────────
# Global Events (Jahreswechsel, Mindestlohnerhöhung, etc.)
# ─────────────────────────────────────────

class GlobalEvent(Base):
    """
    Globale Events wie Jahreswechsel oder Mindestlohnerhöhung,
    die zusätzliche Workflow-Schritte für alle betroffenen Mandanten erzeugen.
    """
    __tablename__ = "global_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)  # null = systemweit
    
    typ = Column(Enum(GlobalEventTyp), nullable=False)
    name = Column(String(255), nullable=False)  # z.B. "Jahreswechsel 2026/2027"
    beschreibung = Column(Text, nullable=True)
    
    # Zeitraum des Events
    gueltig_von = Column(DateTime, nullable=False)  # Ab wann das Event gilt
    gueltig_bis = Column(DateTime, nullable=True)    # Bis wann (null = unbefristet)
    
    # Betroffene Monate (JSON Array: [{"monat": 12, "jahr": 2026}, {"monat": 1, "jahr": 2027}])
    betroffene_monate = Column(Text, nullable=True)
    
    # Filter für betroffene Mandanten (JSON)
    # { "branchen": ["Baugewerbe"], "kategorien": ["A", "B"], "alle": true }
    mandanten_filter = Column(Text, nullable=True)
    
    # Priorität bei mehreren Events
    prioritaet = Column(Integer, default=0)
    
    # Status
    ist_aktiv = Column(Boolean, default=True)
    ist_abgeschlossen = Column(Boolean, default=False)
    
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])
    schritte = relationship("GlobalEventSchritt", back_populates="event", order_by="GlobalEventSchritt.position", cascade="all, delete-orphan")
    workflow_instanzen = relationship("WorkflowInstanz", secondary=workflow_instanz_global_events, back_populates="global_events")


class GlobalEventSchritt(Base):
    """
    Zusätzlicher Workflow-Schritt für ein globales Event.
    Wird automatisch in betroffene Workflow-Instanzen eingespielt.
    """
    __tablename__ = "global_event_schritte"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("global_events.id"), nullable=False)
    
    position = Column(Integer, nullable=False)
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text, nullable=True)
    schritttyp = Column(Enum(WorkflowSchrittTyp), default=WorkflowSchrittTyp.VERARBEITUNG)
    
    # Wann soll dieser Schritt eingefügt werden?
    # "nach_schritt": ID des Vorlage-Items nach dem eingefügt wird
    # "vor_abschluss": Vor dem Abschluss-Schritt
    # "am_anfang": Ganz am Anfang
    einfuege_position = Column(String(50), default="vor_abschluss")
    referenz_schritt_id = Column(Integer, nullable=True)  # Optional: ID des Referenz-Schritts
    
    # Deadline konfiguration
    faellig_offset_tage = Column(Integer, default=0)  # Relativ zum Monatsbeginn
    fristart_referenz = Column(String(100), nullable=True)
    fristart_offset_tage = Column(Integer, default=0)
    
    # Eigenschaften
    ist_pflicht = Column(Boolean, default=True)
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)  # 4-Augen-Prinzip
    verantwortlich_rolle = Column(Enum(UserRole), nullable=True)
    
    # Punkte
    standard_punkte = Column(Float, default=1.0)
    
    # Zusätzliche Hinweise/Anleitungen
    anleitung = Column(Text, nullable=True)
    
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("GlobalEvent", back_populates="schritte")


# ─────────────────────────────────────────
# Branchenspezifische Workflow-Schritte
# ─────────────────────────────────────────

class BranchenWorkflowSchritt(Base):
    """
    Branchenspezifische Workflow-Schritte, die automatisch für alle
    Mandanten einer bestimmten Branche hinzugefügt werden.
    """
    __tablename__ = "branchen_workflow_schritte"

    id = Column(Integer, primary_key=True, index=True)
    branche_id = Column(Integer, ForeignKey("branchen.id"), nullable=False)
    
    position = Column(Integer, nullable=False)
    titel = Column(String(255), nullable=False)
    beschreibung = Column(Text, nullable=True)
    schritttyp = Column(Enum(WorkflowSchrittTyp), default=WorkflowSchrittTyp.VERARBEITUNG)
    
    # Einfüge-Position im Standard-Workflow
    einfuege_position = Column(String(50), default="vor_abschluss")
    referenz_schritt_id = Column(Integer, nullable=True)
    
    # Deadline-Konfiguration
    faellig_offset_tage = Column(Integer, default=0)
    fristart_referenz = Column(String(100), nullable=True)
    fristart_offset_tage = Column(Integer, default=0)
    
    # Eigenschaften
    ist_pflicht = Column(Boolean, default=True)
    ist_optional_pro_mandant = Column(Boolean, default=False)  # Kann pro Mandant deaktiviert werden
    erfordert_dokument = Column(Boolean, default=False)
    erfordert_pruefung = Column(Boolean, default=False)
    verantwortlich_rolle = Column(Enum(UserRole), nullable=True)
    
    # Punkte
    standard_punkte = Column(Float, default=1.0)
    
    # Gültigkeit
    gueltig_von = Column(DateTime, nullable=True)  # Ab wann gilt dieser Schritt
    gueltig_bis = Column(DateTime, nullable=True)  # Bis wann
    
    ist_aktiv = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branche = relationship("Branche", backref="workflow_schritte")


# ─────────────────────────────────────────
# Workflow-Schritt Herkunft (Tracking der Quellen)
# ─────────────────────────────────────────

class WorkflowItemHerkunft(Base):
    """
    Speichert die Herkunft eines Workflow-Items:
    - Standard (aus Vorlage)
    - Branchenspezifisch
    - Mandantenspezifisch
    - Globales Event
    """
    __tablename__ = "workflow_item_herkunft"

    id = Column(Integer, primary_key=True, index=True)
    workflow_item_id = Column(Integer, ForeignKey("workflow_items.id"), nullable=False)
    
    ebene = Column(Enum(WorkflowSchrittEbene), nullable=False)
    
    # Referenz je nach Ebene
    vorlage_item_id = Column(Integer, ForeignKey("workflow_vorlage_items.id"), nullable=True)
    branchen_schritt_id = Column(Integer, ForeignKey("branchen_workflow_schritte.id"), nullable=True)
    mandant_schritt_id = Column(Integer, ForeignKey("mandant_workflow_schritte.id"), nullable=True)
    global_event_schritt_id = Column(Integer, ForeignKey("global_event_schritte.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workflow_item = relationship("WorkflowItem", backref="herkunft")
    vorlage_item = relationship("WorkflowVorlageItem", foreign_keys=[vorlage_item_id])
    branchen_schritt = relationship("BranchenWorkflowSchritt", foreign_keys=[branchen_schritt_id])
    mandant_schritt = relationship("MandantWorkflowSchritt", foreign_keys=[mandant_schritt_id])
    global_event_schritt = relationship("GlobalEventSchritt", foreign_keys=[global_event_schritt_id])
