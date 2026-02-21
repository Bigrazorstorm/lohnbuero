from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_staff
from app.database import get_db
from app.models import (
    Ampelstatus, Mandant, Ticket, TicketPrioritaet, TicketStatus,
    User, WorkflowInstanz, WorkflowStatus
)
from app.schemas import DashboardStats, MandantAmpelInfo

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
