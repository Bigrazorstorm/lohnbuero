from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import (
    Ampelstatus, ChecklistItemStatus, Mandant, Ticket, TicketPrioritaet,
    TicketStatus, User, UserRole, WorkflowInstanz, WorkflowItem,
    WorkflowStatus, WorkflowVorlage, WorkflowVorlageItem,
)
from app.schemas import (
    WorkflowInstanzCreate, WorkflowInstanzOut, WorkflowInstanzShort,
    WorkflowInstanzUpdate, WorkflowItemUpdate, WorkflowItemOut,
    WorkflowVorlageCreate, WorkflowVorlageOut, WorkflowVorlageUpdate,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

_OPEN_TICKET_STATUSES = {
    TicketStatus.NEU,
    TicketStatus.OFFEN,
    TicketStatus.IN_BEARBEITUNG,
    TicketStatus.WARTET_AUF_MANDANT,
    TicketStatus.INTERN_IN_KLAERUNG,
}


# ─── Vorlagen ───────────────────────────────────────────────

@router.get("/vorlagen", response_model=List[WorkflowVorlageOut])
def list_vorlagen(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return db.query(WorkflowVorlage).all()


@router.post("/vorlagen", response_model=WorkflowVorlageOut, status_code=status.HTTP_201_CREATED)
def create_vorlage(
    data: WorkflowVorlageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    vorlage = WorkflowVorlage(
        name=data.name,
        beschreibung=data.beschreibung,
        branche=data.branche,
        ist_standard=data.ist_standard,
        ist_onboarding=data.ist_onboarding,
        erstellt_von_id=current_user.id,
    )
    db.add(vorlage)
    db.flush()

    for item_data in data.items:
        item = WorkflowVorlageItem(vorlage_id=vorlage.id, **item_data.model_dump())
        db.add(item)

    db.commit()
    db.refresh(vorlage)
    return vorlage


@router.get("/vorlagen/{vorlage_id}", response_model=WorkflowVorlageOut)
def get_vorlage(vorlage_id: int, db: Session = Depends(get_db), _: User = Depends(require_staff)):
    vorlage = db.query(WorkflowVorlage).filter(WorkflowVorlage.id == vorlage_id).first()
    if not vorlage:
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    return vorlage


@router.patch("/vorlagen/{vorlage_id}", response_model=WorkflowVorlageOut)
def update_vorlage(
    vorlage_id: int,
    data: WorkflowVorlageUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    vorlage = db.query(WorkflowVorlage).filter(WorkflowVorlage.id == vorlage_id).first()
    if not vorlage:
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(vorlage, k, v)
    db.commit()
    db.refresh(vorlage)
    return vorlage


# ─── Instanzen ───────────────────────────────────────────────

@router.get("/", response_model=List[WorkflowInstanzShort])
def list_workflows(
    mandant_id: Optional[int] = Query(None),
    monat: Optional[int] = Query(None),
    jahr: Optional[int] = Query(None),
    status_filter: Optional[WorkflowStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(WorkflowInstanz)

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if mandant:
            q = q.filter(WorkflowInstanz.mandant_id == mandant.id)
        else:
            return []
    else:
        if mandant_id:
            q = q.filter(WorkflowInstanz.mandant_id == mandant_id)

    if monat:
        q = q.filter(WorkflowInstanz.monat == monat)
    if jahr:
        q = q.filter(WorkflowInstanz.jahr == jahr)
    if status_filter:
        q = q.filter(WorkflowInstanz.status == status_filter)

    return q.order_by(WorkflowInstanz.jahr.desc(), WorkflowInstanz.monat.desc()).all()


@router.post("/", response_model=WorkflowInstanzOut, status_code=status.HTTP_201_CREATED)
def create_workflow(
    data: WorkflowInstanzCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    mandant = db.query(Mandant).filter(Mandant.id == data.mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    # Check duplicate
    existing = db.query(WorkflowInstanz).filter(
        WorkflowInstanz.mandant_id == data.mandant_id,
        WorkflowInstanz.monat == data.monat,
        WorkflowInstanz.jahr == data.jahr,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Workflow für diesen Monat bereits vorhanden")

    instanz = WorkflowInstanz(
        mandant_id=data.mandant_id,
        vorlage_id=data.vorlage_id,
        monat=data.monat,
        jahr=data.jahr,
        sachbearbeiter_id=data.sachbearbeiter_id or mandant.sachbearbeiter_id,
        pruefer_id=data.pruefer_id,
        notizen=data.notizen,
    )
    db.add(instanz)
    db.flush()

    # Create items from template
    vorlage_id = data.vorlage_id
    if not vorlage_id:
        vorlage = db.query(WorkflowVorlage).filter(WorkflowVorlage.ist_standard == True).first()
        if vorlage:
            vorlage_id = vorlage.id

    if vorlage_id:
        vorlage_items = (
            db.query(WorkflowVorlageItem)
            .filter(WorkflowVorlageItem.vorlage_id == vorlage_id)
            .order_by(WorkflowVorlageItem.position)
            .all()
        )
        month_start = datetime(data.jahr, data.monat, 1)
        for vi in vorlage_items:
            faellig = month_start + timedelta(days=vi.faellig_offset_tage) if vi.faellig_offset_tage else None
            item = WorkflowItem(
                instanz_id=instanz.id,
                vorlage_item_id=vi.id,
                position=vi.position,
                titel=vi.titel,
                beschreibung=vi.beschreibung,
                verantwortlich_rolle=vi.verantwortlich_rolle,
                faellig_datum=faellig,
                ist_pflicht=vi.ist_pflicht,
                erfordert_dokument=vi.erfordert_dokument,
                erfordert_pruefung=vi.erfordert_pruefung,
            )
            db.add(item)

    audit_service.log(
        db,
        objekt_typ="workflow",
        objekt_id=instanz.id,
        mandant_id=instanz.mandant_id,
        monat=instanz.monat,
        jahr=instanz.jahr,
        aktionstyp="generiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"monat": instanz.monat, "jahr": instanz.jahr},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Workflow {instanz.monat}/{instanz.jahr} für Mandant {instanz.mandant_id} erstellt",
    )
    db.commit()
    db.refresh(instanz)
    return instanz


@router.get("/{instanz_id}", response_model=WorkflowInstanzOut)
def get_workflow(
    instanz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    instanz = db.query(WorkflowInstanz).filter(WorkflowInstanz.id == instanz_id).first()
    if not instanz:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if not mandant or mandant.id != instanz.mandant_id:
            raise HTTPException(status_code=403, detail="Keine Berechtigung")

    return instanz


@router.patch("/{instanz_id}", response_model=WorkflowInstanzOut)
def update_workflow(
    instanz_id: int,
    data: WorkflowInstanzUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    instanz = db.query(WorkflowInstanz).filter(WorkflowInstanz.id == instanz_id).first()
    if not instanz:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old_status = instanz.status
    new_status = update_data.get("status")

    # ── Month-end closing validation ─────────────────────────
    if new_status == WorkflowStatus.ABGESCHLOSSEN and old_status != WorkflowStatus.ABGESCHLOSSEN:
        errors = _validate_monatsabschluss(db, instanz)
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"message": "Monatsabschluss nicht möglich", "fehler": errors},
            )
        update_data["abgeschlossen_am"] = datetime.utcnow()

    # ── Re-open requires a reason ─────────────────────────────
    if old_status == WorkflowStatus.ABGESCHLOSSEN and new_status and new_status != WorkflowStatus.ABGESCHLOSSEN:
        begruendung = update_data.get("wiedereroeffnet_begruendung") or instanz.wiedereroeffnet_begruendung
        if not begruendung:
            raise HTTPException(status_code=400, detail="Begründung für Wiederöffnung erforderlich")
        update_data["wiedereroeffnet_am"] = datetime.utcnow()

    for k, v in update_data.items():
        setattr(instanz, k, v)

    audit_service.log(
        db,
        objekt_typ="workflow",
        objekt_id=instanz.id,
        mandant_id=instanz.mandant_id,
        monat=instanz.monat,
        jahr=instanz.jahr,
        aktionstyp="statuswechsel" if new_status else "aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"status": old_status} if new_status else None,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Workflow {instanz.monat}/{instanz.jahr} geändert",
    )
    db.commit()
    db.refresh(instanz)
    return instanz


def _validate_monatsabschluss(db: Session, instanz: WorkflowInstanz) -> list:
    """Return list of blocking errors for month-end closing."""
    errors = []

    # 1. All mandatory workflow items must be done
    open_pflicht = [
        i for i in instanz.items
        if i.ist_pflicht and i.status != ChecklistItemStatus.ERLEDIGT
    ]
    if open_pflicht:
        errors.append(f"{len(open_pflicht)} Pflicht-Schritte noch nicht erledigt")

    # 2. If a prüfer is set, the proof step must be confirmed
    if instanz.pruefer_id and not instanz.probe_geprueft_am:
        errors.append("4-Augen-Prüfung noch nicht abgeschlossen")

    # 3. No open critical tickets for this workflow's month
    kritische_offen = db.query(Ticket).filter(
        Ticket.mandant_id == instanz.mandant_id,
        Ticket.monat == instanz.monat,
        Ticket.jahr == instanz.jahr,
        Ticket.prioritaet == TicketPrioritaet.KRITISCH,
        Ticket.status.in_(list(_OPEN_TICKET_STATUSES)),
    ).count()
    if kritische_offen:
        errors.append(f"{kritische_offen} kritische Ticket(s) noch offen")

    return errors


# ─── Workflow Items (Checklist) ───────────────────────────────

@router.patch("/{instanz_id}/items/{item_id}", response_model=WorkflowItemOut)
def update_workflow_item(
    instanz_id: int,
    item_id: int,
    data: WorkflowItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(WorkflowItem).filter(
        WorkflowItem.id == item_id,
        WorkflowItem.instanz_id == instanz_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist-Item nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old_status = item.status

    if "status" in update_data:
        if update_data["status"] == ChecklistItemStatus.ERLEDIGT:
            item.erledigt_am = datetime.utcnow()
            item.erledigt_von_id = current_user.id
            # Add points
            points = item.punkte or 1.0  # Default 1 if not set
            current_user.total_points_earned += points
            current_user.current_workload -= points
            item.instanz.punkte += points
        elif item.status == ChecklistItemStatus.ERLEDIGT:
            item.erledigt_am = None
            item.erledigt_von_id = None
            # Subtract points if undone
            points = item.punkte or 1.0
            current_user.total_points_earned -= points
            current_user.current_workload += points
            item.instanz.punkte -= points

    for k, v in update_data.items():
        setattr(item, k, v)

    # Update parent workflow ampelstatus
    _update_ampel(db, instanz_id)

    audit_service.log(
        db,
        objekt_typ="workflow_item",
        objekt_id=item.id,
        mandant_id=item.instanz.mandant_id if item.instanz else None,
        monat=item.instanz.monat if item.instanz else None,
        jahr=item.instanz.jahr if item.instanz else None,
        aktionstyp="statusaenderung",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"status": old_status},
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Workflow-Schritt '{item.titel}' → {update_data.get('status', old_status)}",
    )
    db.commit()
    db.refresh(item)
    return item


def _update_ampel(db: Session, instanz_id: int):
    """Recompute Ampelstatus based on overdue items."""
    instanz = db.query(WorkflowInstanz).filter(WorkflowInstanz.id == instanz_id).first()
    if not instanz or instanz.status == WorkflowStatus.ABGESCHLOSSEN:
        return

    now = datetime.utcnow()
    open_items = [
        i for i in instanz.items
        if i.status == ChecklistItemStatus.OFFEN and i.ist_pflicht
    ]
    overdue = [i for i in open_items if i.faellig_datum and i.faellig_datum < now]
    warning = [
        i for i in open_items
        if i.faellig_datum and now <= i.faellig_datum <= now + timedelta(days=2)
    ]

    # Check for blocking tickets
    critical_tickets = db.query(Ticket).filter(
        Ticket.mandant_id == instanz.mandant_id,
        Ticket.workflow_instanz_id == instanz_id,
        Ticket.prioritaet == TicketPrioritaet.KRITISCH,
        Ticket.status.in_(OPEN_STATUSES)
    ).count() > 0

    if overdue or critical_tickets:
        instanz.ampelstatus = Ampelstatus.ROT
    elif warning:
        instanz.ampelstatus = Ampelstatus.GELB
    else:
        instanz.ampelstatus = Ampelstatus.GRUEN


# ─── Bulk create monthly workflows ───────────────────────────

@router.post("/bulk-create-monthly", response_model=List[WorkflowInstanzShort])
def bulk_create_monthly(
    monat: int = Query(..., ge=1, le=12),
    jahr: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    """Create workflows for all active mandanten for a given month."""
    mandanten = db.query(Mandant).filter(Mandant.ist_aktiv == True).all()
    standard_vorlage = db.query(WorkflowVorlage).filter(WorkflowVorlage.ist_standard == True).first()

    created = []
    for mandant in mandanten:
        existing = db.query(WorkflowInstanz).filter(
            WorkflowInstanz.mandant_id == mandant.id,
            WorkflowInstanz.monat == monat,
            WorkflowInstanz.jahr == jahr,
        ).first()
        if existing:
            continue

        instanz = WorkflowInstanz(
            mandant_id=mandant.id,
            vorlage_id=standard_vorlage.id if standard_vorlage else None,
            monat=monat,
            jahr=jahr,
            sachbearbeiter_id=mandant.sachbearbeiter_id,
        )
        db.add(instanz)
        db.flush()

        if standard_vorlage:
            month_start = datetime(jahr, monat, 1)
            for vi in standard_vorlage.items:
                faellig = month_start + timedelta(days=vi.faellig_offset_tage) if vi.faellig_offset_tage else None
                item = WorkflowItem(
                    instanz_id=instanz.id,
                    vorlage_item_id=vi.id,
                    position=vi.position,
                    titel=vi.titel,
                    beschreibung=vi.beschreibung,
                    verantwortlich_rolle=vi.verantwortlich_rolle,
                    faellig_datum=faellig,
                    ist_pflicht=vi.ist_pflicht,
                    erfordert_dokument=vi.erfordert_dokument,
                    erfordert_pruefung=vi.erfordert_pruefung,
                )
                db.add(item)

        audit_service.log(
            db,
            objekt_typ="workflow",
            objekt_id=instanz.id,
            mandant_id=mandant.id,
            monat=monat,
            jahr=jahr,
            aktionstyp="bulk_generiert",
            benutzer_id=current_user.id,
            benutzerrolle=current_user.role.value,
            beschreibung=f"Workflow {monat}/{jahr} per Bulk für Mandant {mandant.id} erstellt",
        )
        created.append(instanz)

    db.commit()
    for inst in created:
        db.refresh(inst)

    return created
