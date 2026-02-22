"""Seed system defaults for all admin configuration areas."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    AusgabewegConfig, Branche, EmailTemplate, FristenVorlage,
    SmtpKonfiguration, SystemDefault, UploadKonfiguration,
    WorkflowSchrittTyp, PunkteKonfiguration,
)


DEFAULT_BRANCHEN = [
    {"name": "Baugewerbe", "faktor": 1.3, "soka_relevant": True, "tags": '["SOKA-BAU","Bauhauptgewerbe"]'},
    {"name": "Gastronomie", "faktor": 1.1, "soka_relevant": False, "tags": '["Minijobs","Trinkgeld"]'},
    {"name": "Handwerk", "faktor": 1.0, "soka_relevant": False, "tags": '["Innungen"]'},
    {"name": "Einzelhandel", "faktor": 0.9, "soka_relevant": False, "tags": '["Teilzeit"]'},
    {"name": "IT / Software", "faktor": 1.0, "soka_relevant": False, "tags": '["bAV","Sachbezüge"]'},
    {"name": "Gesundheitswesen", "faktor": 1.2, "soka_relevant": False, "tags": '["Schichtarbeit","Zuschläge"]'},
    {"name": "Logistik / Transport", "faktor": 1.1, "soka_relevant": False, "tags": '["Spesen","Fernfahrer"]'},
    {"name": "Produktion / Industrie", "faktor": 1.1, "soka_relevant": False, "tags": '["Schichtmodelle","Tarif"]'},
    {"name": "Dienstleistung", "faktor": 1.0, "soka_relevant": False, "tags": '[]'},
    {"name": "Öffentlicher Dienst", "faktor": 1.2, "soka_relevant": False, "tags": '["TVöD","Zusatzversorgung"]'},
]

DEFAULT_AUSGABEWEGE = [
    {"name": "E-Mail", "beschreibung": "Versand der Auswertungen per E-Mail", "beeinflusst_workflow": False},
    {"name": "Portal", "beschreibung": "Bereitstellung über das Mandantenportal", "beeinflusst_workflow": True, "zusatz_workflow_schritt": "Upload ins Portal"},
    {"name": "Post", "beschreibung": "Postalischer Versand", "beeinflusst_workflow": False},
    {"name": "DMS-Link", "beschreibung": "Bereitstellung als DMS-Link", "beeinflusst_workflow": False},
    {"name": "Addison-Export", "beschreibung": "Export direkt aus Addison", "beeinflusst_workflow": False},
    {"name": "Dateiserver/SharePoint", "beschreibung": "Ablage auf Dateiserver oder SharePoint", "beeinflusst_workflow": False},
]

DEFAULT_EMAIL_TEMPLATES = [
    {
        "name": "Onboarding Begrüßung",
        "typ": "onboarding_welcome",
        "betreff": "Willkommen bei {{KanzleiName}} – Ihr Lohn-Service",
        "html_inhalt": "<h2>Herzlich willkommen, {{Ansprechpartner}}!</h2><p>Wir freuen uns, Sie als Mandant bei {{KanzleiName}} begrüßen zu dürfen.</p><p>Ihr Sachbearbeiter <strong>{{SachbearbeiterName}}</strong> steht Ihnen für alle Fragen zur Verfügung.</p><p>Über das Portal können Sie Ihre Unterlagen einreichen: <a href='{{PortalLink}}'>Zum Portal</a></p>",
        "text_inhalt": "Herzlich willkommen, {{Ansprechpartner}}! Wir freuen uns, Sie als Mandant begrüßen zu dürfen. Ihr Sachbearbeiter {{SachbearbeiterName}} steht Ihnen zur Verfügung.",
        "beschreibung": "Begrüßungsmail für neue Mandanten",
        "reihenfolge": 1,
    },
    {
        "name": "Aktivierungserinnerung",
        "typ": "onboarding_reminder",
        "betreff": "Erinnerung: Portal-Aktivierung für {{Mandantenname}}",
        "html_inhalt": "<p>Lieber {{Ansprechpartner}},</p><p>wir möchten Sie daran erinnern, Ihren Portal-Zugang zu aktivieren: <a href='{{PortalLink}}'>Jetzt aktivieren</a></p>",
        "text_inhalt": "Lieber {{Ansprechpartner}}, bitte aktivieren Sie Ihren Portal-Zugang unter {{PortalLink}}.",
        "beschreibung": "Erinnerung zur Portal-Aktivierung",
        "reihenfolge": 2,
        "verzoegerung_tage": 3,
    },
    {
        "name": "Unterlagen-Reminder",
        "typ": "unterlagen_reminder",
        "betreff": "Erinnerung: Unterlagen für {{Monat}} – {{Mandantenname}}",
        "html_inhalt": "<p>Lieber {{Ansprechpartner}},</p><p>bitte reichen Sie die Lohnunterlagen für den Monat <strong>{{Monat}}</strong> bis zum <strong>{{Fristdatum}}</strong> ein.</p><p><a href='{{PortalLink}}'>Unterlagen hochladen</a></p>",
        "text_inhalt": "Bitte reichen Sie die Lohnunterlagen für {{Monat}} bis zum {{Fristdatum}} ein.",
        "beschreibung": "Monatliche Erinnerung für Unterlagen-Einreichung",
        "reihenfolge": 0,
    },
    {
        "name": "Neues Ticket",
        "typ": "ticket_neu",
        "betreff": "Neue Rückfrage zu {{Mandantenname}} – Ticket #{{TicketID}}",
        "html_inhalt": "<p>Es wurde eine neue Rückfrage erstellt:</p><p><strong>Ticket #{{TicketID}}</strong></p><p>Bitte antworten Sie über das Portal: <a href='{{PortalLink}}'>Zum Ticket</a></p>",
        "text_inhalt": "Neue Rückfrage: Ticket #{{TicketID}} für {{Mandantenname}}. Bitte antworten Sie über das Portal.",
        "beschreibung": "Benachrichtigung bei neuem Ticket",
        "reihenfolge": 0,
    },
    {
        "name": "Ticket-Antwort",
        "typ": "ticket_antwort",
        "betreff": "Antwort auf Ticket #{{TicketID}} – {{Mandantenname}}",
        "html_inhalt": "<p>Ihr Ticket #{{TicketID}} wurde beantwortet.</p><p><a href='{{PortalLink}}'>Antwort ansehen</a></p>",
        "text_inhalt": "Ihr Ticket #{{TicketID}} wurde beantwortet. Bitte prüfen Sie die Antwort im Portal.",
        "beschreibung": "Benachrichtigung bei Ticket-Antwort",
        "reihenfolge": 0,
    },
    {
        "name": "Ticket-Eskalation",
        "typ": "ticket_eskalation",
        "betreff": "ESKALATION: Ticket #{{TicketID}} – {{Mandantenname}}",
        "html_inhalt": "<p><strong>Achtung:</strong> Ticket #{{TicketID}} wurde eskaliert.</p><p>Bitte umgehend bearbeiten.</p>",
        "text_inhalt": "ESKALATION: Ticket #{{TicketID}} für {{Mandantenname}} wurde eskaliert. Bitte umgehend bearbeiten.",
        "beschreibung": "Benachrichtigung bei Ticket-Eskalation",
        "reihenfolge": 0,
    },
    {
        "name": "Frist-Reminder intern",
        "typ": "frist_reminder_intern",
        "betreff": "Frist-Erinnerung: {{Mandantenname}} – Abgabe am {{Fristdatum}}",
        "html_inhalt": "<p>Die Abgabefrist für <strong>{{Mandantenname}}</strong> ist am <strong>{{Fristdatum}}</strong>.</p><p>Bitte stellen Sie die rechtzeitige Bearbeitung sicher.</p>",
        "text_inhalt": "Frist-Erinnerung: {{Mandantenname}} – Abgabe am {{Fristdatum}}. Bitte rechtzeitig bearbeiten.",
        "beschreibung": "Interne Frist-Erinnerung für Sachbearbeiter",
        "reihenfolge": 0,
    },
    {
        "name": "Frist-Reminder Mandant",
        "typ": "frist_reminder_mandant",
        "betreff": "Erinnerung: Unterlagen bis {{Fristdatum}} einreichen",
        "html_inhalt": "<p>Lieber {{Ansprechpartner}},</p><p>bitte reichen Sie die ausstehenden Unterlagen bis zum <strong>{{Fristdatum}}</strong> ein.</p>",
        "text_inhalt": "Bitte reichen Sie die ausstehenden Unterlagen bis zum {{Fristdatum}} ein.",
        "beschreibung": "Frist-Erinnerung an Mandanten",
        "reihenfolge": 0,
    },
]

# ─────────────────────────────────────────
# Default German Deadline Templates (Section 2.3)
# ─────────────────────────────────────────

DEFAULT_FRISTEN_VORLAGEN = [
    {
        "code": "PAY_DAY",
        "name": "Lohnzahlung (Pay Day)",
        "beschreibung": "Mandantenspezifischer Lohnzahlungstag. Häufig Monatsende oder X. des Folgemonats.",
        "regeltyp": "relativ_monatsende",
        "regel_config": json.dumps({"tage_nach_monatsende": 0}),
        "default_interne_vorfrist_tage": 3,
    },
    {
        "code": "SV_ZAHLUNG",
        "name": "SV-Beitragszahlung",
        "beschreibung": "Drittletzter Bankarbeitstag des Monats. Bankarbeitstage je nach Sitz der Einzugsstelle.",
        "regeltyp": "relativ_bankarbeitstage",
        "regel_config": json.dumps({"n_ter_letzter": 3}),
        "default_interne_vorfrist_tage": 2,
    },
    {
        "code": "SV_NACHWEIS",
        "name": "SV-Beitragsnachweis",
        "beschreibung": "Spätestens Beginn des fünftletzten Bankarbeitstags des Monats.",
        "regeltyp": "relativ_bankarbeitstage",
        "regel_config": json.dumps({"n_ter_letzter": 5}),
        "default_interne_vorfrist_tage": 2,
    },
    {
        "code": "LOHNSTEUER",
        "name": "Lohnsteuer-Anmeldung & Zahlung",
        "beschreibung": "Spätestens am 10. Tag nach Ablauf des Anmeldezeitraums. Verschiebung auf nächsten Werktag bei Sa/So/Feiertag.",
        "regeltyp": "fixes_datum",
        "regel_config": json.dumps({"tag": 10, "monat_offset": 1, "verschiebung_naechster_werktag": True}),
        "default_interne_vorfrist_tage": 2,
        "anmeldezeitraum": "monatlich",
    },
    {
        "code": "SOKA_MELDUNG",
        "name": "SOKA-BAU Monatsmeldung",
        "beschreibung": "Monatsmeldung bis 15. des Folgemonats. Nur für SOKA-relevante Mandanten.",
        "regeltyp": "fixes_datum",
        "regel_config": json.dumps({"tag": 15, "monat_offset": 1}),
        "default_interne_vorfrist_tage": 2,
        "branchenfilter": "SOKA",
    },
    {
        "code": "SOKA_ZAHLUNG",
        "name": "SOKA-BAU Zahlung",
        "beschreibung": "Zahlung bis 28. des Folgemonats. Nur für SOKA-relevante Mandanten.",
        "regeltyp": "fixes_datum",
        "regel_config": json.dumps({"tag": 28, "monat_offset": 1}),
        "default_interne_vorfrist_tage": 2,
        "branchenfilter": "SOKA",
    },
    {
        "code": "DEUEV_JAHRESMELDUNG",
        "name": "DEÜV-Jahresmeldung",
        "beschreibung": "Spätestens 15. Februar des Folgejahres.",
        "regeltyp": "fixes_datum",
        "regel_config": json.dumps({"tag": 15, "monat_offset": 0}),
        "default_interne_vorfrist_tage": 5,
        "ist_jahresbezogen": True,
    },
    {
        "code": "DEUEV_ANMELDUNG",
        "name": "DEÜV-Anmeldung",
        "beschreibung": "Mit nächster Abrechnung, spätestens 6 Wochen nach Beschäftigungsbeginn.",
        "regeltyp": "ereignisbasiert",
        "regel_config": json.dumps({"trigger": "neueintritt", "max_frist_wochen": 6}),
        "default_interne_vorfrist_tage": 2,
        "ist_ereignisbasiert": True,
    },
    {
        "code": "DEUEV_SOFORTMELDUNG",
        "name": "DEÜV-Sofortmeldung",
        "beschreibung": "Spätestens bis Aufnahme der Beschäftigung (branchenabhängig).",
        "regeltyp": "ereignisbasiert",
        "regel_config": json.dumps({"trigger": "neueintritt", "sofort": True}),
        "default_interne_vorfrist_tage": 0,
        "ist_ereignisbasiert": True,
    },
    {
        "code": "UV_LOHNNACHWEIS",
        "name": "UV – Lohnnachweis digital",
        "beschreibung": "Abgabe bis 16. Februar des Folgejahres.",
        "regeltyp": "fixes_datum",
        "regel_config": json.dumps({"tag": 16, "monat_offset": 0}),
        "default_interne_vorfrist_tage": 5,
        "ist_jahresbezogen": True,
    },
]

# ─────────────────────────────────────────
# Default Workflow Step Types (Section 8)
# ─────────────────────────────────────────

DEFAULT_WORKFLOW_SCHRITT_TYPEN = [
    {"name": "Unterlagen anfordern", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "fristart_referenz": "PAY_DAY", "fristart_offset_tage": -10, "standard_punkte": 1.0},
    {"name": "Datenerfassung", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "standard_punkte": 2.0},
    {"name": "Probeabrechnung", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "standard_punkte": 2.0},
    {"name": "4-Augen-Prüfung", "ist_pflicht": False, "standard_rolle": "pruefer", "abhaengigkeit_von": "Probeabrechnung", "standard_punkte": 1.5},
    {"name": "SV-Beitragsnachweis erstellen", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "fristart_referenz": "SV_NACHWEIS", "fristart_offset_tage": 0, "standard_punkte": 1.0},
    {"name": "Lohnsteuer anmelden", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "fristart_referenz": "LOHNSTEUER", "fristart_offset_tage": 0, "standard_punkte": 1.0},
    {"name": "Mandantenfreigabe", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "standard_punkte": 0.5},
    {"name": "Endabrechnung", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "standard_punkte": 1.5},
    {"name": "SOKA-Meldung erstellen", "ist_pflicht": False, "standard_rolle": "sachbearbeiter", "fristart_referenz": "SOKA_MELDUNG", "fristart_offset_tage": 0, "standard_punkte": 1.0},
    {"name": "Versand / Export", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "standard_punkte": 0.5},
    {"name": "Monatsabschluss", "ist_pflicht": True, "standard_rolle": "sachbearbeiter", "abhaengigkeit_von": "Endabrechnung", "standard_punkte": 0.5},
]

# ─────────────────────────────────────────
# Default Punkte-Konfiguration (Section 4.4)
# ─────────────────────────────────────────

DEFAULT_PUNKTE_KONFIGURATION = {
    "name": "Standard-Punktekonfiguration",
    "kategorie_basis": json.dumps({"A": 10, "B": 5, "C": 3}),
    "mitarbeiter_stufen": json.dumps([
        {"bis": 10, "faktor": 1.0},
        {"bis": 50, "faktor": 1.5},
        {"bis": 100, "faktor": 2.0},
        {"bis": 500, "faktor": 3.0},
        {"bis": 99999, "faktor": 4.0},
    ]),
    "branchen_faktoren": json.dumps({
        "Baugewerbe": 1.3,
        "Gastronomie": 1.1,
        "Gesundheitswesen": 1.2,
        "Öffentlicher Dienst": 1.2,
    }),
    "zusatzmodul_punkte": json.dumps({
        "viele_eintritte": 2.0,
        "einmalzahlungen": 1.0,
        "kurzarbeit": 3.0,
        "bav": 1.5,
        "pfaendungen": 2.0,
    }),
}

SYSTEM_DEFAULT_CONFIGS = [
    {"bereich": "branchen", "name": "Basis-Branchenliste", "konfiguration": json.dumps({"count": len(DEFAULT_BRANCHEN), "source": "system"})},
    {"bereich": "ausgabewege", "name": "Basis-Ausgabewege", "konfiguration": json.dumps({"count": len(DEFAULT_AUSGABEWEGE), "source": "system"})},
    {"bereich": "fristen", "name": "Default-Fristenkatalog", "konfiguration": json.dumps({
        "typen": [fv["code"] for fv in DEFAULT_FRISTEN_VORLAGEN],
        "count": len(DEFAULT_FRISTEN_VORLAGEN),
    })},
    {"bereich": "workflow", "name": "Default-Workflow-Schritte", "konfiguration": json.dumps({
        "typen": [st["name"] for st in DEFAULT_WORKFLOW_SCHRITT_TYPEN],
        "count": len(DEFAULT_WORKFLOW_SCHRITT_TYPEN),
    })},
    {"bereich": "punkte", "name": "Basis-Punktekonfiguration", "konfiguration": json.dumps({
        "basis_punkte_pro_mitarbeiter": 1.0,
        "faktoren": {"SOKA": 1.3, "Kurzarbeit": 1.2, "bAV": 1.1},
    })},
    {"bereich": "tickets", "name": "Ticket-Konfiguration", "konfiguration": json.dumps({
        "kategorien": ["Fehlende Unterlagen", "Rückfrage", "Korrektur", "Eskalation", "Sonstiges"],
        "unterkategorien": {"Fehlende Unterlagen": ["Lohnzettel", "Krankmeldung", "Reisekosten"], "Korrektur": ["Nachberechnung", "Stornierung"]},
        "prioritaeten": ["niedrig", "normal", "hoch", "kritisch", "dringend"],
        "status_modell": ["neu", "offen", "in_bearbeitung", "wartet_auf_mandant", "wartet_intern", "intern_in_klaerung", "in_pruefung", "beantwortet", "geloest", "geschlossen", "abgebrochen"],
    })},
    {"bereich": "email_templates", "name": "Standard-E-Mail-Templates", "konfiguration": json.dumps({
        "count": len(DEFAULT_EMAIL_TEMPLATES),
        "typen": [t["typ"] for t in DEFAULT_EMAIL_TEMPLATES],
    })},
    {"bereich": "upload", "name": "Upload-Konfiguration", "konfiguration": json.dumps({
        "max_dateigroesse_mb": 10,
        "erlaubte_dateitypen": ["pdf", "doc", "docx", "xls", "xlsx", "csv", "jpg", "jpeg", "png", "txt", "zip"],
    })},
]


def seed_defaults_for_bereich(db: Session, bereich: str):
    """Seed or reset defaults for a specific configuration area."""
    if bereich == "branchen":
        for bd in DEFAULT_BRANCHEN:
            existing = db.query(Branche).filter(Branche.name == bd["name"]).first()
            if not existing:
                db.add(Branche(**bd))

    elif bereich == "ausgabewege":
        for ad in DEFAULT_AUSGABEWEGE:
            existing = db.query(AusgabewegConfig).filter(AusgabewegConfig.name == ad["name"]).first()
            if not existing:
                db.add(AusgabewegConfig(**ad))

    elif bereich == "email_templates":
        for td in DEFAULT_EMAIL_TEMPLATES:
            existing = db.query(EmailTemplate).filter(EmailTemplate.typ == td["typ"]).first()
            if not existing:
                db.add(EmailTemplate(**td))

    elif bereich == "fristen":
        for fv in DEFAULT_FRISTEN_VORLAGEN:
            existing = db.query(FristenVorlage).filter(FristenVorlage.code == fv["code"]).first()
            if not existing:
                db.add(FristenVorlage(**fv))

    elif bereich == "workflow_schritte":
        for st in DEFAULT_WORKFLOW_SCHRITT_TYPEN:
            existing = db.query(WorkflowSchrittTyp).filter(WorkflowSchrittTyp.name == st["name"]).first()
            if not existing:
                db.add(WorkflowSchrittTyp(**st))

    elif bereich == "punkte":
        existing = db.query(PunkteKonfiguration).filter(PunkteKonfiguration.name == DEFAULT_PUNKTE_KONFIGURATION["name"]).first()
        if not existing:
            db.add(PunkteKonfiguration(**DEFAULT_PUNKTE_KONFIGURATION))

    # Update system_defaults record
    sd = db.query(SystemDefault).filter(
        SystemDefault.bereich == bereich,
    ).first()
    config_entry = next((c for c in SYSTEM_DEFAULT_CONFIGS if c["bereich"] == bereich), None)
    if config_entry:
        if sd:
            sd.konfiguration = config_entry["konfiguration"]
            sd.updated_at = datetime.utcnow()
        else:
            db.add(SystemDefault(**config_entry))


def seed_all_defaults(db: Session):
    """Seed all default configuration data."""
    # Branchen
    for bd in DEFAULT_BRANCHEN:
        existing = db.query(Branche).filter(Branche.name == bd["name"]).first()
        if not existing:
            db.add(Branche(**bd))

    # Ausgabewege
    for ad in DEFAULT_AUSGABEWEGE:
        existing = db.query(AusgabewegConfig).filter(AusgabewegConfig.name == ad["name"]).first()
        if not existing:
            db.add(AusgabewegConfig(**ad))

    # Email Templates (only if none exist)
    if db.query(EmailTemplate).count() == 0:
        for td in DEFAULT_EMAIL_TEMPLATES:
            db.add(EmailTemplate(**td))

    # Fristen-Vorlagen (default DE deadline templates)
    for fv in DEFAULT_FRISTEN_VORLAGEN:
        existing = db.query(FristenVorlage).filter(FristenVorlage.code == fv["code"]).first()
        if not existing:
            db.add(FristenVorlage(**fv))

    # Workflow-Schritt-Typen
    for st in DEFAULT_WORKFLOW_SCHRITT_TYPEN:
        existing = db.query(WorkflowSchrittTyp).filter(WorkflowSchrittTyp.name == st["name"]).first()
        if not existing:
            db.add(WorkflowSchrittTyp(**st))

    # Punkte-Konfiguration
    existing = db.query(PunkteKonfiguration).filter(PunkteKonfiguration.name == DEFAULT_PUNKTE_KONFIGURATION["name"]).first()
    if not existing:
        db.add(PunkteKonfiguration(**DEFAULT_PUNKTE_KONFIGURATION))

    # System Defaults
    for sd_config in SYSTEM_DEFAULT_CONFIGS:
        existing = db.query(SystemDefault).filter(
            SystemDefault.bereich == sd_config["bereich"],
            SystemDefault.name == sd_config["name"],
        ).first()
        if not existing:
            db.add(SystemDefault(**sd_config))

    # Upload config
    if db.query(UploadKonfiguration).count() == 0:
        db.add(UploadKonfiguration())
