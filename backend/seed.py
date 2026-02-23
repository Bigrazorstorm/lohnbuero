"""Seed the database with initial demo data."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from app.database import SessionLocal, engine
from app.models import User, UserRole, Mandant, MandantKategorie, Abgabeweg
from app.models import WorkflowVorlage, WorkflowVorlageItem, WorkflowInstanz, WorkflowItem
from app.models import Ticket, TicketPrioritaet, TicketStatus, WorkflowStatus, Ampelstatus
from app.auth import get_password_hash


def seed(db=None):
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        if db.query(User).count() > 0:
            print("Database already seeded, skipping.")
            return

        print("Seeding database...")

        # ── Users ─────────────────────────────────────────────
        admin = User(
            email="admin@kanzlei.de",
            full_name="Maria Müller",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("admin123"),
        )
        teamleitung = User(
            email="teamleitung@kanzlei.de",
            full_name="Thomas Weber",
            role=UserRole.TEAMLEITUNG,
            hashed_password=get_password_hash("team123"),
        )
        sb1 = User(
            email="anna.schmidt@kanzlei.de",
            full_name="Anna Schmidt",
            role=UserRole.SACHBEARBEITER,
            hashed_password=get_password_hash("sb123"),
        )
        sb2 = User(
            email="peter.hoffmann@kanzlei.de",
            full_name="Peter Hoffmann",
            role=UserRole.SACHBEARBEITER,
            hashed_password=get_password_hash("sb123"),
        )
        pruefer = User(
            email="pruefer@kanzlei.de",
            full_name="Klaus Fischer",
            role=UserRole.PRUEFER,
            hashed_password=get_password_hash("pruef123"),
        )
        mandant_user = User(
            email="buchhaltung@baufirma.de",
            full_name="Baufirma Meier – Portal",
            role=UserRole.MANDANT,
            hashed_password=get_password_hash("mandant123"),
        )

        for u in [admin, teamleitung, sb1, sb2, pruefer, mandant_user]:
            db.add(u)
        db.commit()

        # ── Workflow-Vorlage (Standard) ────────────────────────
        vorlage = WorkflowVorlage(
            name="Standard Lohnabrechnung",
            beschreibung="Standardprozess für die monatliche Lohnabrechnung",
            ist_standard=True,
            erstellt_von_id=admin.id,
        )
        db.add(vorlage)
        db.flush()

        vorlage_items = [
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=1, titel="Bewegungsdaten anfordern",
                beschreibung="Mandant kontaktieren und Bewegungsdaten (An-/Abwesenheiten, Sonderzahlungen) anfordern",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=2, ist_pflicht=True, erfordert_dokument=False),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=2, titel="Unterlagen vollständig eingegangen",
                beschreibung="Vollständigkeitscheck: Alle Bewegungsdaten, Krankmeldungen, Stundennachweise vorhanden",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=5, ist_pflicht=True, erfordert_dokument=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=3, titel="Erfassung in Addison",
                beschreibung="Bewegungsdaten in Addison Lohn & Gehalt erfassen",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=8, ist_pflicht=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=4, titel="Probeabrechnung erstellen",
                beschreibung="Probeabrechnung in Addison erstellen und intern prüfen",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=10, ist_pflicht=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=5, titel="4-Augen-Prüfung Probeabrechnung",
                beschreibung="Probeabrechnung durch Prüfer kontrollieren",
                verantwortlich_rolle=UserRole.PRUEFER, faellig_offset_tage=11, ist_pflicht=False, erfordert_pruefung=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=6, titel="Mandantenfreigabe einholen",
                beschreibung="Probeabrechnung an Mandant senden und Freigabe dokumentieren",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=12, ist_pflicht=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=7, titel="Endabrechnung in Addison",
                beschreibung="Endabrechnung durchführen nach Mandantenfreigabe",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=13, ist_pflicht=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=8, titel="Versand Lohnzettel & Buchungslisten",
                beschreibung="Lohnzettel und Buchungslisten versenden/bereitstellen",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=14, ist_pflicht=True),
            WorkflowVorlageItem(vorlage_id=vorlage.id, position=9, titel="Monatsabschluss dokumentieren",
                beschreibung="Archivierung, Protokoll erstellen, Bearbeitungszeit erfassen",
                verantwortlich_rolle=UserRole.SACHBEARBEITER, faellig_offset_tage=15, ist_pflicht=True),
        ]
        for item in vorlage_items:
            db.add(item)
        db.commit()

        # ── Mandanten ──────────────────────────────────────────
        m1 = Mandant(
            nummer="10001",
            name="Baufirma Meier GmbH",
            branche="Baugewerbe",
            ansprechpartner_name="Hans Meier",
            ansprechpartner_email="buchhaltung@baufirma.de",
            ansprechpartner_telefon="030 123456",
            lohnabschluss_tag=15,
            abgabeweg=Abgabeweg.PORTAL,
            kategorie=MandantKategorie.A,
            service_level="Premium",
            mitarbeiteranzahl=48,
            besonderheiten="SOKA-BAU Meldungen, mehrere Kostenstelllen",
            sachbearbeiter_id=sb1.id,
            vertretung_id=sb2.id,
            portal_user_id=mandant_user.id,
            monatspauschale=380.0,
        )
        m2 = Mandant(
            nummer="10002",
            name="Restaurant Zum Goldenen Hirsch",
            branche="Gastronomie",
            ansprechpartner_name="Sabine Goldmann",
            ansprechpartner_email="info@goldener-hirsch.de",
            ansprechpartner_telefon="089 987654",
            lohnabschluss_tag=12,
            abgabeweg=Abgabeweg.EMAIL,
            kategorie=MandantKategorie.B,
            mitarbeiteranzahl=12,
            besonderheiten="Kurzarbeit Stammdaten, häufig wechselnde Aushilfen",
            sachbearbeiter_id=sb1.id,
            vertretung_id=sb2.id,
            monatspauschale=160.0,
        )
        m3 = Mandant(
            nummer="10003",
            name="IT-Solutions KG",
            branche="IT / Software",
            ansprechpartner_name="Dr. Frank Braun",
            ansprechpartner_email="hr@it-solutions.de",
            ansprechpartner_telefon="040 555000",
            lohnabschluss_tag=18,
            abgabeweg=Abgabeweg.EMAIL,
            kategorie=MandantKategorie.A,
            service_level="Standard",
            mitarbeiteranzahl=35,
            besonderheiten="Sachbezüge, bAV, verschiedene Arbeitszeitmodelle",
            sachbearbeiter_id=sb2.id,
            vertretung_id=sb1.id,
            monatspauschale=290.0,
        )
        m4 = Mandant(
            nummer="10004",
            name="Blumenhaus Sonnenblume",
            branche="Einzelhandel",
            ansprechpartner_name="Ute Blume",
            ansprechpartner_email="ute@sonnenblume.de",
            ansprechpartner_telefon="0711 334455",
            lohnabschluss_tag=10,
            abgabeweg=Abgabeweg.POST,
            kategorie=MandantKategorie.C,
            mitarbeiteranzahl=3,
            monatspauschale=65.0,
        )
        m5 = Mandant(
            nummer="10005",
            name="Sanitär Meister Krug",
            branche="Handwerk",
            ansprechpartner_name="Werner Krug",
            ansprechpartner_email="krug@sanitaer-krug.de",
            ansprechpartner_telefon="0231 776699",
            lohnabschluss_tag=14,
            abgabeweg=Abgabeweg.EMAIL,
            kategorie=MandantKategorie.B,
            mitarbeiteranzahl=8,
            besonderheiten="Vermögenswirksame Leistungen für alle MA",
            sachbearbeiter_id=sb2.id,
            monatspauschale=120.0,
        )

        for m in [m1, m2, m3, m4, m5]:
            db.add(m)
        db.commit()

        # ── Workflow Instanzen (aktueller Monat) ───────────────
        now = datetime.utcnow()
        monat = now.month
        jahr = now.year
        month_start = datetime(jahr, monat, 1)

        def make_workflow(mandant, status=WorkflowStatus.IN_BEARBEITUNG, ampel=Ampelstatus.GRUEN,
                          done_items=3):
            inst = WorkflowInstanz(
                mandant_id=mandant.id,
                vorlage_id=vorlage.id,
                monat=monat,
                jahr=jahr,
                status=status,
                ampelstatus=ampel,
                sachbearbeiter_id=mandant.sachbearbeiter_id,
                pruefer_id=pruefer.id,
            )
            db.add(inst)
            db.flush()

            for i, vi in enumerate(vorlage_items):
                item_status = "erledigt" if i < done_items else "offen"
                from app.models import ChecklistItemStatus
                witem = WorkflowItem(
                    instanz_id=inst.id,
                    vorlage_item_id=vi.id,
                    position=vi.position,
                    titel=vi.titel,
                    beschreibung=vi.beschreibung,
                    verantwortlich_rolle=vi.verantwortlich_rolle,
                    faellig_datum=month_start + timedelta(days=vi.faellig_offset_tage),
                    ist_pflicht=vi.ist_pflicht,
                    erfordert_dokument=vi.erfordert_dokument,
                    erfordert_pruefung=vi.erfordert_pruefung,
                    status=ChecklistItemStatus.ERLEDIGT if i < done_items else ChecklistItemStatus.OFFEN,
                    erledigt_am=now - timedelta(days=5) if i < done_items else None,
                    erledigt_von_id=mandant.sachbearbeiter_id if i < done_items else None,
                )
                db.add(witem)

            if status == WorkflowStatus.IN_BEARBEITUNG:
                inst.unterlagen_eingegangen_am = now - timedelta(days=4)
            return inst

        wf1 = make_workflow(m1, WorkflowStatus.IN_BEARBEITUNG, Ampelstatus.GELB, done_items=4)
        wf2 = make_workflow(m2, WorkflowStatus.IN_BEARBEITUNG, Ampelstatus.ROT, done_items=1)
        wf3 = make_workflow(m3, WorkflowStatus.IN_BEARBEITUNG, Ampelstatus.GRUEN, done_items=6)
        wf4 = make_workflow(m4, WorkflowStatus.OFFEN, Ampelstatus.GRUEN, done_items=0)
        wf5 = make_workflow(m5, WorkflowStatus.ESKALIERT, Ampelstatus.ROT, done_items=2)
        db.commit()

        # ── Tickets ────────────────────────────────────────────
        t1 = Ticket(
            mandant_id=m2.id,
            workflow_instanz_id=wf2.id,
            erstellt_von_id=sb1.id,
            titel="Stundennachweise fehlen für Februar",
            beschreibung="Die Stundennachweise für alle Minijobber wurden noch nicht eingereicht. Bitte bis 05.02. nachreichen.",
            status=TicketStatus.OFFEN,
            prioritaet=TicketPrioritaet.DRINGEND,
            kategorie="Fehlende Unterlagen",
            faellig_bis=month_start + timedelta(days=5),
        )
        t2 = Ticket(
            mandant_id=m1.id,
            workflow_instanz_id=wf1.id,
            erstellt_von_id=sb1.id,
            zugewiesen_an_id=mandant_user.id,
            titel="Klärung Sonderzahlung Prämie",
            beschreibung="Ist die im Vormonat angekündigte Prämie für MA Schmidt in diesem Monat auszuzahlen?",
            status=TicketStatus.BEANTWORTET,
            prioritaet=TicketPrioritaet.NORMAL,
            kategorie="Rückfrage",
        )
        t3 = Ticket(
            mandant_id=m5.id,
            workflow_instanz_id=wf5.id,
            erstellt_von_id=teamleitung.id,
            titel="Unterlagen seit 5 Tagen überfällig – Eskalation",
            beschreibung="Trotz mehrfacher Erinnerung wurden keine Unterlagen eingereicht. Teamleitung informiert.",
            status=TicketStatus.IN_BEARBEITUNG,
            prioritaet=TicketPrioritaet.DRINGEND,
            kategorie="Eskalation",
        )

        for t in [t1, t2, t3]:
            db.add(t)
        db.commit()

        print("✓ Seed complete!")
        print("\nDemo accounts:")
        print("  admin@kanzlei.de        / admin123   (Admin)")
        print("  teamleitung@kanzlei.de  / team123    (Teamleitung)")
        print("  anna.schmidt@kanzlei.de / sb123      (Sachbearbeiter)")
        print("  pruefer@kanzlei.de      / pruef123   (Prüfer)")
        print("  buchhaltung@baufirma.de / mandant123 (Mandant-Portal)")
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed()
