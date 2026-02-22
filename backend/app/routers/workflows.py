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
from app.workflow_service import WorkflowService

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
    """Create a new workflow instance from template with smart deadline calculation."""
    mandant = db.query(Mandant).filter(Mandant.id == data.mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    # Check for duplicate
    existing = db.query(WorkflowInstanz).filter(
        WorkflowInstanz.mandant_id == data.mandant_id,
        WorkflowInstanz.monat == data.monat,
        WorkflowInstanz.jahr == data.jahr,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Workflow für diesen Monat bereits vorhanden")

    # Use WorkflowService to create workflow with calculated deadlines
    service = WorkflowService(db)
    try:
        instanz = service.create_workflow_from_template(
            mandant_id=data.mandant_id,
            vorlage_id=data.vorlage_id,
            monat=data.monat,
            jahr=data.jahr,
            sachbearbeiter_id=data.sachbearbeiter_id,
            pruefer_id=data.pruefer_id,
        )
        
        # Set notes if provided
        if data.notizen:
            instanz.notizen = data.notizen
        
        db.commit()
        db.refresh(instanz)
        
        audit_service.log(
            db,
            objekt_typ="workflow",
            objekt_id=instanz.id,
            mandant_id=instanz.mandant_id,
            monat=instanz.monat,
            jahr=instanz.jahr,
            aktionstyp="erstellt",
            benutzer_id=current_user.id,
            benutzerrolle=current_user.role.value,
            neuer_wert={"monat": instanz.monat, "jahr": instanz.jahr, "sla_deadline": instanz.sla_deadline.isoformat() if instanz.sla_deadline else None},
            ip_adresse=request.client.host if request.client else None,
            beschreibung=f"Workflow {instanz.monat}/{instanz.jahr} für Mandant {instanz.mandant_id} erstellt (mit SLA-Berechnung)",
        )
        
        return instanz
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    """Update a workflow instance with enhanced validation and service integration."""
    instanz = db.query(WorkflowInstanz).filter(WorkflowInstanz.id == instanz_id).first()
    if not instanz:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")

    service = WorkflowService(db)
    update_data = data.model_dump(exclude_unset=True)
    old_status = instanz.status
    new_status = update_data.get("status")

    # ── Determine step type (kernel process vs item) ─────────────────────────
    KERNEL_PROCESS_KEYS = {
        'unterlagen_eingegangen_am': 'unterlagen_eingegangen_von_id',
        'probe_abrechnung_am': 'probe_abrechnung_von_id',
        'probe_geprueft_am': 'probe_geprueft_von_id',
        'mandant_freigabe_am': 'mandant_freigabe_von_id',
        'endabrechnung_am': 'endabrechnung_von_id',
        'versand_am': 'versand_von_id',
        'abgeschlossen_am': 'abgeschlossen_von_id'
    }

    kernel_updates = {k: v for k, v in update_data.items() if k in KERNEL_PROCESS_KEYS}
    is_kernel_update = bool(kernel_updates)

    # ── Set "von" user for kernel process steps ──────────────────────────────
    if is_kernel_update:
        for key, value in kernel_updates.items():
            von_field = KERNEL_PROCESS_KEYS[key]
            if value is not None:
                update_data[von_field] = current_user.id
            else:
                update_data[von_field] = None

    # ── Closing validation ───────────────────────────────────────────────────
    if new_status == WorkflowStatus.ABGESCHLOSSEN and old_status != WorkflowStatus.ABGESCHLOSSEN:
        can_close, errors = service.validate_can_close(instanz)
        if not can_close:
            raise HTTPException(
                status_code=400,
                detail={"message": "Monatsabschluss nicht möglich", "fehler": errors},
            )
        update_data["abgeschlossen_am"] = datetime.utcnow()

    # ── Re-opening logic ─────────────────────────────────────────────────────
    if old_status == WorkflowStatus.ABGESCHLOSSEN and new_status and new_status != WorkflowStatus.ABGESCHLOSSEN:
        begruendung = update_data.get("wiedereroeffnet_begruendung") or instanz.wiedereroeffnet_begruendung
        if not begruendung:
            raise HTTPException(status_code=400, detail="Begründung für Wiederöffnung erforderlich")
        update_data["wiedereroeffnet_am"] = datetime.utcnow()

    # ── Apply updates ────────────────────────────────────────────────────────
    for k, v in update_data.items():
        setattr(instanz, k, v)

    # ── Automatically update ampel status ────────────────────────────────────
    service.update_ampel_status_with_log(instanz_id)

    # ── Audit logging ────────────────────────────────────────────────────────
    if is_kernel_update:
        audit_service.log(
            db,
            objekt_typ="workflow",
            objekt_id=instanz.id,
            mandant_id=instanz.mandant_id,
            monat=instanz.monat,
            jahr=instanz.jahr,
            aktionstyp="kernprozess",
            benutzer_id=current_user.id,
            benutzerrolle=current_user.role.value,
            neuer_wert=kernel_updates,
            ip_adresse=request.client.host if request.client else None,
            beschreibung=f"Kernprozess-Schritte aktualisiert für Workflow {instanz.monat}/{instanz.jahr}",
        )
    else:
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
            beschreibung=f"Workflow {instanz.monat}/{instanz.jahr} aktualisiert",
        )
    
    db.commit()
    db.refresh(instanz)
    return instanz


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
        aktionstyp="item_status",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"status": old_status},
        neuer_wert={"status": update_data.get("status"), "titel": item.titel},
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
        Ticket.status.in_(_OPEN_TICKET_STATUSES)
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
    """Create workflows for ALL active mandants for a given month with smart deadline calculation."""
    service = WorkflowService(db)
    mandanten = db.query(Mandant).filter(Mandant.ist_aktiv == True).all()

    created = []
    for mandant in mandanten:
        # Skip if workflow already exists
        existing = db.query(WorkflowInstanz).filter(
            WorkflowInstanz.mandant_id == mandant.id,
            WorkflowInstanz.monat == monat,
            WorkflowInstanz.jahr == jahr,
        ).first()
        if existing:
            continue

        try:
            instanz = service.create_workflow_from_template(
                mandant_id=mandant.id,
                vorlage_id=None,  # Will find suitable template
                monat=monat,
                jahr=jahr,
                sachbearbeiter_id=mandant.sachbearbeiter_id,
            )
            
            audit_service.log(
                db,
                objekt_typ="workflow",
                objekt_id=instanz.id,
                mandant_id=mandant.id,
                monat=monat,
                jahr=jahr,
                aktionstyp="bulk_erstellt",
                benutzer_id=current_user.id,
                benutzerrolle=current_user.role.value,
                beschreibung=f"Workflow {monat}/{jahr} per Bulk für Mandant {mandant.id} erstellt",
            )
            
            created.append(instanz)
        except Exception as e:
            # Log error but continue with other mandants
            print(f"Error creating workflow for mandant {mandant.id}: {str(e)}")
            continue

    db.commit()
    for inst in created:
        db.refresh(inst)

    return created

