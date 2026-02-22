from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_staff
from app.database import get_db
from app.models import (
    EskalationStufe, Mandant, SLAKonfiguration, Ticket,
    TicketKommentar, TicketPrioritaet, TicketStatus, User, UserRole,
)
from app.schemas import (
    TicketCreate, TicketKommentarCreate, TicketKommentarOut,
    TicketOut, TicketUpdate,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

# Ordered list of statuses considered "active" (not yet closed/resolved)
OPEN_STATUSES = {
    TicketStatus.NEU,
    TicketStatus.OFFEN,
    TicketStatus.IN_BEARBEITUNG,
    TicketStatus.WARTET_AUF_MANDANT,
    TicketStatus.INTERN_IN_KLAERUNG,
}

CRITICAL_STATUSES = OPEN_STATUSES  # any open ticket with prioritaet=KRITISCH blocks month-end


def _client_visible_kommentare(kommentare, is_mandant: bool):
    """Filter out internal comments for mandant-role users."""
    if not is_mandant:
        return kommentare
    return [k for k in kommentare if not k.ist_intern]


@router.get("/", response_model=List[TicketOut])
def list_tickets(
    mandant_id: Optional[int] = Query(None),
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    prioritaet: Optional[TicketPrioritaet] = Query(None),
    eskaliert: Optional[bool] = Query(None),
    monat: Optional[int] = Query(None),
    jahr: Optional[int] = Query(None),
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
    if prioritaet:
        q = q.filter(Ticket.prioritaet == prioritaet)
    if eskaliert is not None:
        if eskaliert:
            q = q.filter(Ticket.eskalationsstufe.isnot(None))
        else:
            q = q.filter(Ticket.eskalationsstufe.is_(None))
    if monat:
        q = q.filter(Ticket.monat == monat)
    if jahr:
        q = q.filter(Ticket.jahr == jahr)

    tickets = q.order_by(Ticket.created_at.desc()).all()

    # Hide internal comments from mandant role
    if current_user.role == UserRole.MANDANT:
        for t in tickets:
            t.kommentare = _client_visible_kommentare(t.kommentare, True)

    return tickets


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    data: TicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mandant = db.query(Mandant).filter(Mandant.id == data.mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    if current_user.role == UserRole.MANDANT and mandant.portal_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    # Determine SLA deadline from configuration
    faellig_bis = data.faellig_bis
    if not faellig_bis and data.kategorie:
        sla_cfg = db.query(SLAKonfiguration).filter(
            SLAKonfiguration.kategorie == data.kategorie,
        ).first()
        if sla_cfg:
            from datetime import timedelta
            faellig_bis = datetime.utcnow() + timedelta(hours=sla_cfg.sla_stunden)

    ticket = Ticket(
        **{k: v for k, v in data.model_dump().items() if k != "faellig_bis"},
        faellig_bis=faellig_bis,
        erstellt_von_id=current_user.id,
        status=TicketStatus.NEU,
    )
    db.add(ticket)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="ticket",
        objekt_id=ticket.id,
        mandant_id=ticket.mandant_id,
        monat=ticket.monat,
        jahr=ticket.jahr,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"titel": ticket.titel, "prioritaet": ticket.prioritaet, "kategorie": ticket.kategorie},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Ticket '{ticket.titel}' erstellt",
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/kpis")
def ticket_kpis(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Ticket KPIs – no time-tracking, only counts and system-time differences."""
    from sqlalchemy import func, case
    total = db.query(Ticket).count()
    offen = db.query(Ticket).filter(Ticket.status.in_(list(OPEN_STATUSES))).count()
    eskaliert = db.query(Ticket).filter(Ticket.eskalationsstufe.isnot(None)).count()
    kritisch_offen = db.query(Ticket).filter(
        Ticket.prioritaet == TicketPrioritaet.KRITISCH,
        Ticket.status.in_(list(OPEN_STATUSES)),
    ).count()

    # Average response time (hours) = avg(first comment time - ticket creation time)
    # Only tickets that have at least one comment
    from sqlalchemy import select
    first_kommentar_subq = (
        db.query(
            TicketKommentar.ticket_id,
            func.min(TicketKommentar.created_at).label("first_at"),
        )
        .group_by(TicketKommentar.ticket_id)
        .subquery()
    )
    avg_response_hours = None
    rows = (
        db.query(Ticket.created_at, first_kommentar_subq.c.first_at)
        .join(first_kommentar_subq, Ticket.id == first_kommentar_subq.c.ticket_id)
        .all()
    )
    if rows:
        deltas = [
            (r.first_at - r.created_at).total_seconds() / 3600
            for r in rows if r.first_at > r.created_at
        ]
        avg_response_hours = round(sum(deltas) / len(deltas), 1) if deltas else None

    return {
        "gesamt": total,
        "offen": offen,
        "eskaliert": eskaliert,
        "kritisch_offen": kritisch_offen,
        "avg_antwortzeit_stunden": avg_response_hours,
    }


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
        ticket.kommentare = _client_visible_kommentare(ticket.kommentare, True)

    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old_status = ticket.status
    old_prio = ticket.prioritaet

    if update_data.get("status") == TicketStatus.GESCHLOSSEN and ticket.status != TicketStatus.GESCHLOSSEN:
        update_data["geschlossen_am"] = datetime.utcnow()
        update_data["eskalationsstufe"] = None

    for k, v in update_data.items():
        setattr(ticket, k, v)

    ticket.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="ticket",
        objekt_id=ticket.id,
        mandant_id=ticket.mandant_id,
        monat=ticket.monat,
        jahr=ticket.jahr,
        aktionstyp="geaendert",
        benutzer_id=None,
        benutzerrolle=None,
        alter_wert={"status": old_status, "prioritaet": old_prio},
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Ticket #{ticket.id} aktualisiert",
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/eskalieren", response_model=TicketOut)
def eskaliere_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

    current = ticket.eskalationsstufe
    if current is None:
        new_stufe = EskalationStufe.TEAMLEITUNG
    elif current == EskalationStufe.TEAMLEITUNG:
        new_stufe = EskalationStufe.LEITUNG
    else:
        raise HTTPException(status_code=400, detail="Ticket bereits auf höchster Eskalationsstufe")

    ticket.eskalationsstufe = new_stufe
    ticket.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="ticket",
        objekt_id=ticket.id,
        mandant_id=ticket.mandant_id,
        monat=ticket.monat,
        jahr=ticket.jahr,
        aktionstyp="eskalation",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"eskalationsstufe": current},
        neuer_wert={"eskalationsstufe": new_stufe},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Ticket #{ticket.id} eskaliert auf {new_stufe.value}",
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/kommentare", response_model=TicketKommentarOut, status_code=status.HTTP_201_CREATED)
def add_kommentar(
    ticket_id: int,
    data: TicketKommentarCreate,
    request: Request,
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
        # Mandant cannot post internal comments
        if data.ist_intern:
            raise HTTPException(status_code=403, detail="Mandanten können keine internen Kommentare verfassen")

    # Validate quote reference
    if data.zitat_id:
        zitat = db.query(TicketKommentar).filter(
            TicketKommentar.id == data.zitat_id,
            TicketKommentar.ticket_id == ticket_id,
        ).first()
        if not zitat:
            raise HTTPException(status_code=404, detail="Zitierter Kommentar nicht gefunden")

    kommentar = TicketKommentar(
        ticket_id=ticket_id,
        autor_id=current_user.id,
        inhalt=data.inhalt,
        ist_intern=data.ist_intern,
        zitat_id=data.zitat_id,
    )
    db.add(kommentar)

    # Auto-update ticket status
    if current_user.role == UserRole.MANDANT:
        if ticket.status == TicketStatus.WARTET_AUF_MANDANT:
            ticket.status = TicketStatus.INTERN_IN_KLAERUNG
    else:
        if ticket.status in (TicketStatus.NEU, TicketStatus.OFFEN):
            ticket.status = TicketStatus.INTERN_IN_KLAERUNG

    ticket.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="ticket",
        objekt_id=ticket.id,
        mandant_id=ticket.mandant_id,
        monat=ticket.monat,
        jahr=ticket.jahr,
        aktionstyp="kommentar_intern" if data.ist_intern else "mandantenantwort" if current_user.role == UserRole.MANDANT else "kommentar",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"inhalt_laenge": len(data.inhalt), "ist_intern": data.ist_intern},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"{'Interner Kommentar' if data.ist_intern else 'Kommentar'} zu Ticket #{ticket.id}",
    )
    db.commit()
    db.refresh(kommentar)
    return kommentar
