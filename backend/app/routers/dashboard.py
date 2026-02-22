from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_staff, get_current_user
from app.database import get_db
from app.models import (
    Ampelstatus, Mandant, Sonderaufgabe, Ticket, TicketPrioritaet, TicketStatus,
    User, WorkflowInstanz, WorkflowItem, WorkflowStatus
)
from app.schemas import (
    DashboardMeinTag, DashboardStats, KritischInfo, 
    MandantAmpelInfo, MeineArbeitItem, WartetAufMandantInfo
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    now = datetime.utcnow()
    monat = now.month
    jahr = now.year

    mandanten_gesamt = db.query(Mandant).count()
    mandanten_aktiv = db.query(Mandant).filter(Mandant.ist_aktiv == True).count()

    current_workflows = db.query(WorkflowInstanz).filter(
        WorkflowInstanz.monat == monat,
        WorkflowInstanz.jahr == jahr,
    )
    workflows_offen = current_workflows.filter(WorkflowInstanz.status == WorkflowStatus.OFFEN).count()
    workflows_in_bearbeitung = current_workflows.filter(
        WorkflowInstanz.status == WorkflowStatus.IN_BEARBEITUNG
    ).count()
    workflows_eskaliert = current_workflows.filter(WorkflowInstanz.status == WorkflowStatus.ESKALIERT).count()

    tickets_offen = db.query(Ticket).filter(
        Ticket.status.in_([TicketStatus.OFFEN, TicketStatus.IN_BEARBEITUNG])
    ).count()
    tickets_dringend = db.query(Ticket).filter(
        Ticket.status.in_([TicketStatus.OFFEN, TicketStatus.IN_BEARBEITUNG]),
        Ticket.prioritaet == TicketPrioritaet.DRINGEND,
    ).count()

    ampel_rot = current_workflows.filter(WorkflowInstanz.ampelstatus == Ampelstatus.ROT).count()
    ampel_gelb = current_workflows.filter(WorkflowInstanz.ampelstatus == Ampelstatus.GELB).count()
    ampel_gruen = current_workflows.filter(WorkflowInstanz.ampelstatus == Ampelstatus.GRUEN).count()

    return DashboardStats(
        mandanten_gesamt=mandanten_gesamt,
        mandanten_aktiv=mandanten_aktiv,
        workflows_offen=workflows_offen,
        workflows_in_bearbeitung=workflows_in_bearbeitung,
        workflows_eskaliert=workflows_eskaliert,
        tickets_offen=tickets_offen,
        tickets_dringend=tickets_dringend,
        ampel_rot=ampel_rot,
        ampel_gelb=ampel_gelb,
        ampel_gruen=ampel_gruen,
    )


@router.get("/ampel", response_model=List[MandantAmpelInfo])
def get_ampel_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Return current month's Ampelstatus per active Mandant."""
    now = datetime.utcnow()
    monat = now.month
    jahr = now.year

    mandanten = db.query(Mandant).filter(Mandant.ist_aktiv == True).order_by(Mandant.kategorie, Mandant.name).all()
    result = []

    for m in mandanten:
        instanz = db.query(WorkflowInstanz).filter(
            WorkflowInstanz.mandant_id == m.id,
            WorkflowInstanz.monat == monat,
            WorkflowInstanz.jahr == jahr,
        ).first()

        info = MandantAmpelInfo(
            mandant_id=m.id,
            mandant_name=m.name,
            mandant_kategorie=m.kategorie,
            ampelstatus=instanz.ampelstatus if instanz else Ampelstatus.GRUEN,
            workflow_id=instanz.id if instanz else None,
            monat=monat if instanz else None,
            jahr=jahr if instanz else None,
            status=instanz.status if instanz else None,
            sachbearbeiter=instanz.sachbearbeiter if instanz else m.sachbearbeiter,
        )
        result.append(info)

    return result


@router.get("/mein-tag", response_model=DashboardMeinTag)
def get_mein_tag(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the 'Mein Tag' (Cockpit) sections: kritisch, wartet auf mandant, meine arbeit."""
    now = datetime.utcnow()
    monat = now.month
    jahr = now.year

    # 1. Kritisch: workflows with ROT or GELB ampelstatus for current month
    kritisch_query = db.query(WorkflowInstanz).filter(
        WorkflowInstanz.monat == monat,
        WorkflowInstanz.jahr == jahr,
        WorkflowInstanz.ampelstatus.in_([Ampelstatus.ROT, Ampelstatus.GELB])
    ).order_by(
        # ROT first, then by earliest deadline
        WorkflowInstanz.ampelstatus,
        WorkflowInstanz.unterlagen_eingegangen_am.asc().nullsfirst()
    ).limit(20)

    kritisch = []
    for wf in kritisch_query:
        # Find next deadline (simple: use first incomplete item with date, or fallback to month end)
        naechster_stichtag = None
        stichtag_typ = None
        blocker = None

        # Check for blockers
        if wf.blocker_indikatoren:
            blocker = "; ".join([b.beschreibung for b in wf.blocker_indikatoren])

        # Find first incomplete workflow item with a due date
        for item in wf.items:
            if item.status.name in ('offen', 'in_bearbeitung') and item.faellig_datum:
                naechster_stichtag = item.faellig_datum.strftime('%Y-%m-%d') if isinstance(item.faellig_datum, datetime) else str(item.faellig_datum)
                stichtag_typ = item.titel
                break

        # Fallback: use workflow month end as implicit deadline
        if not naechster_stichtag:
            next_month = datetime(jahr, monat, 1) + timedelta(days=32)
            last_day = next_month.replace(day=1) - timedelta(days=1)
            naechster_stichtag = last_day.strftime('%Y-%m-%d')
            stichtag_typ = "Monatsende"

        kritisch.append(KritischInfo(
            mandant_id=wf.mandant_id,
            mandant_name=wf.mandant.name if wf.mandant else "Unbekannt",
            mandant_kategorie=wf.mandant.kategorie if wf.mandant else 'C',
            workflow_id=wf.id,
            monat=wf.monat,
            jahr=wf.jahr,
            naechster_stichtag=naechster_stichtag,
            stichtag_typ=stichtag_typ,
            ampelstatus=wf.ampelstatus,
            sachbearbeiter=wf.sachbearbeiter,
            blocker=blocker
        ))

    # 2. Wartet auf Mandant: tickets with status wartet_auf_mandant
    wartet_query = db.query(Ticket).filter(
        Ticket.status == TicketStatus.WARTET_AUF_MANDANT
    ).order_by(Ticket.updated_at.asc()).limit(20)

    wartet_auf_mandant = []
    for t in wartet_query:
        # Find related workflow
        wf = None
        if t.workflow_instanz_id:
            wf = db.query(WorkflowInstanz).filter(WorkflowInstanz.id == t.workflow_instanz_id).first()

        # Calculate how long waiting
        wartet_seit = None
        if t.updated_at:
            t_age = now - t.updated_at
            if t_age.days > 0:
                wartet_seit = f"{t_age.days} Tage"
            elif t_age.seconds // 3600 > 0:
                wartet_seit = f"{t_age.seconds // 3600} Std"
            else:
                wartet_seit = "Gerade eben"

        wartet_auf_mandant.append(WartetAufMandantInfo(
            mandant_id=t.mandant_id,
            mandant_name=t.mandant.name if t.mandant else "Unbekannt",
            workflow_id=wf.id if wf else 0,
            monat=t.monat or (wf.monat if wf else 0),
            jahr=t.jahr or (wf.jahr if wf else 0),
            ticket_id=t.id,
            ticket_titel=t.titel,
            sachbearbeiter=t.zugewiesen_an,
            wartet_seit=wartet_seit
        ))

    # 3. Meine Arbeit: workflow items assigned to current user + Sonderaufgaben
    meine_arbeit = []

    # 3a. Workflow items assigned to current user
    workflow_items = db.query(WorkflowItem).join(WorkflowInstanz).filter(
        WorkflowInstanz.sachbearbeiter_id == current_user.id,
        WorkflowItem.status.in_(['offen', 'in_bearbeitung'])
    ).order_by(WorkflowItem.faellig_datum.asc().nullsfirst()).limit(20)

    for item in workflow_items:
        wf_instanz = db.query(WorkflowInstanz).filter(WorkflowInstanz.id == item.instanz_id).first()
        if not wf_instanz:
            continue

        # Determine priority based on due date
        prioritaet = "normal"
        if item.faellig_datum:
            days_until = (item.faellig_datum - now).days
            if days_until < 0:
                prioritaet = "kritisch"
            elif days_until <= 2:
                prioritaet = "hoch"

        meine_arbeit.append(MeineArbeitItem(
            typ="workflow_schritt",
            id=item.id,
            titel=item.titel,
            mandant_id=wf_instanz.mandant_id,
            mandant_name=wf_instanz.mandant.name if wf_instanz.mandant else "Unbekannt",
            monat=wf_instanz.monat,
            jahr=wf_instanz.jahr,
            faellig_datum=item.faellig_datum.strftime('%Y-%m-%d') if isinstance(item.faellig_datum, datetime) else str(item.faellig_datum) if item.faellig_datum else None,
            punkte=item.punkte,
            prioritaet=prioritaet
        ))

    # 3b. Sonderaufgaben assigned to current user
    sonderaufgaben = db.query(Sonderaufgabe).filter(
        Sonderaufgabe.verantwortlicher_id == current_user.id,
        Sonderaufgabe.status.in_(['offen', 'in_bearbeitung'])
    ).order_by(Sonderaufgabe.faellig_datum.asc().nullsfirst()).limit(20)

    for sa in sonderaufgaben:
        prioritaet = "normal"
        if sa.faellig_datum:
            days_until = (sa.faellig_datum - now).days
            if days_until < 0:
                prioritaet = "kritisch"
            elif days_until <= 2:
                prioritaet = "hoch"

        meine_arbeit.append(MeineArbeitItem(
            typ="sonderaufgabe",
            id=sa.id,
            titel=sa.titel,
            mandant_id=sa.mandant_id or 0,
            mandant_name=sa.mandant.name if sa.mandant else "Allgemein",
            monat=sa.monat,
            jahr=sa.jahr,
            faellig_datum=sa.faellig_datum.strftime('%Y-%m-%d') if isinstance(sa.faellig_datum, datetime) else str(sa.faellig_datum) if sa.faellig_datum else None,
            punkte=sa.punkte,
            prioritaet=prioritaet
        ))

    # Sort by priority (kritisch first)
    priority_order = {"kritisch": 0, "hoch": 1, "normal": 2}
    meine_arbeit.sort(key=lambda x: priority_order.get(x.prioritaet or "normal", 2))

    return DashboardMeinTag(
        kritisch=kritisch,
        wartet_auf_mandant=wartet_auf_mandant,
        meine_arbeit=meine_arbeit[:20]  # Limit total
    )
