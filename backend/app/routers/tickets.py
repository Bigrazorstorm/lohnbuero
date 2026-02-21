from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_staff
from app.database import get_db
from app.models import Mandant, Ticket, TicketKommentar, TicketStatus, User, UserRole
from app.schemas import (
    TicketCreate, TicketKommentarCreate, TicketKommentarOut, TicketOut, TicketUpdate
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("/", response_model=List[TicketOut])
def list_tickets(
    mandant_id: Optional[int] = Query(None),
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Ticket)

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if mandant:
            q = q.filter(Ticket.mandant_id == mandant.id)
        else:
            return []
    else:
        if mandant_id:
            q = q.filter(Ticket.mandant_id == mandant_id)

    if status_filter:
        q = q.filter(Ticket.status == status_filter)

    return q.order_by(Ticket.created_at.desc()).all()


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mandant = db.query(Mandant).filter(Mandant.id == data.mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    if current_user.role == UserRole.MANDANT and mandant.portal_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    ticket = Ticket(
        **data.model_dump(),
        erstellt_von_id=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if not mandant or mandant.id != ticket.mandant_id:
            raise HTTPException(status_code=403, detail="Keine Berechtigung")

    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("status") == TicketStatus.GESCHLOSSEN and ticket.status != TicketStatus.GESCHLOSSEN:
        update_data["geschlossen_am"] = datetime.utcnow()

    for k, v in update_data.items():
        setattr(ticket, k, v)

    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/kommentare", response_model=TicketKommentarOut, status_code=status.HTTP_201_CREATED)
def add_kommentar(
    ticket_id: int,
    data: TicketKommentarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if not mandant or mandant.id != ticket.mandant_id:
            raise HTTPException(status_code=403, detail="Keine Berechtigung")

    kommentar = TicketKommentar(
        ticket_id=ticket_id,
        autor_id=current_user.id,
        inhalt=data.inhalt,
    )
    db.add(kommentar)

    # Auto-update ticket status
    if ticket.status == TicketStatus.OFFEN and current_user.role != UserRole.MANDANT:
        ticket.status = TicketStatus.IN_BEARBEITUNG
    elif current_user.role == UserRole.MANDANT and ticket.status == TicketStatus.BEANTWORTET:
        ticket.status = TicketStatus.IN_BEARBEITUNG

    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(kommentar)
    return kommentar
