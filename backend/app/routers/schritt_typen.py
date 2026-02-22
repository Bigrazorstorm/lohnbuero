"""Admin-definable workflow step types & mandant-specific activation."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import require_admin, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import (
    MandantWorkflowSchritt, User, WorkflowSchrittTyp, Mandant,
)
from app.schemas import (
    MandantWorkflowSchrittCreate, MandantWorkflowSchrittOut,
    WorkflowSchrittTypCreate, WorkflowSchrittTypOut, WorkflowSchrittTypUpdate,
)

router = APIRouter(prefix="/api/admin/schritt-typen", tags=["workflow-schritt-typen"])


# ─── WorkflowSchrittTyp CRUD ──────────────────────────────────

@router.get("/", response_model=List[WorkflowSchrittTypOut])
def list_schritt_typen(
    aktiv: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    q = db.query(WorkflowSchrittTyp)
    if aktiv is not None:
        q = q.filter(WorkflowSchrittTyp.ist_aktiv == aktiv)
    return q.order_by(WorkflowSchrittTyp.name).all()


@router.post("/", response_model=WorkflowSchrittTypOut, status_code=status.HTTP_201_CREATED)
def create_schritt_typ(
    data: WorkflowSchrittTypCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.query(WorkflowSchrittTyp).filter(WorkflowSchrittTyp.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Schritt-Typ mit diesem Namen existiert bereits")

    typ = WorkflowSchrittTyp(**data.model_dump())
    db.add(typ)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="workflow_schritt_typ",
        objekt_id=typ.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert=data.model_dump(),
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Workflow-Schritt-Typ '{typ.name}' erstellt",
    )
    db.commit()
    db.refresh(typ)
    return typ


@router.get("/{typ_id}", response_model=WorkflowSchrittTypOut)
def get_schritt_typ(
    typ_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    typ = db.query(WorkflowSchrittTyp).filter(WorkflowSchrittTyp.id == typ_id).first()
    if not typ:
        raise HTTPException(status_code=404, detail="Schritt-Typ nicht gefunden")
    return typ


@router.patch("/{typ_id}", response_model=WorkflowSchrittTypOut)
def update_schritt_typ(
    typ_id: int,
    data: WorkflowSchrittTypUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    typ = db.query(WorkflowSchrittTyp).filter(WorkflowSchrittTyp.id == typ_id).first()
    if not typ:
        raise HTTPException(status_code=404, detail="Schritt-Typ nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(typ, k) for k in update_data}

    for k, v in update_data.items():
        setattr(typ, k, v)
    typ.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="workflow_schritt_typ",
        objekt_id=typ.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Workflow-Schritt-Typ '{typ.name}' geändert",
    )
    db.commit()
    db.refresh(typ)
    return typ


# ─── Mandant-specific Step Activation ─────────────────────────

@router.get("/mandant/{mandant_id}", response_model=List[MandantWorkflowSchrittOut])
def list_mandant_schritte(
    mandant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    return db.query(MandantWorkflowSchritt).filter(
        MandantWorkflowSchritt.mandant_id == mandant_id
    ).all()


@router.post("/mandant/{mandant_id}", response_model=MandantWorkflowSchrittOut, status_code=status.HTTP_201_CREATED)
def activate_mandant_schritt(
    mandant_id: int,
    data: MandantWorkflowSchrittCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    typ = db.query(WorkflowSchrittTyp).filter(WorkflowSchrittTyp.id == data.schritt_typ_id).first()
    if not typ:
        raise HTTPException(status_code=404, detail="Schritt-Typ nicht gefunden")

    # Check if already exists
    existing = db.query(MandantWorkflowSchritt).filter(
        MandantWorkflowSchritt.mandant_id == mandant_id,
        MandantWorkflowSchritt.schritt_typ_id == data.schritt_typ_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Schritt-Typ für diesen Mandant bereits konfiguriert")

    schritt = MandantWorkflowSchritt(
        mandant_id=mandant_id,
        erstellt_von_id=current_user.id,
        **data.model_dump(),
    )
    db.add(schritt)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="mandant_workflow_schritt",
        objekt_id=schritt.id,
        mandant_id=mandant_id,
        aktionstyp="aktiviert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"schritt_typ": typ.name, "ist_aktiv": data.ist_aktiv, "aenderung_zum": str(data.aenderung_zum) if data.aenderung_zum else None},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Workflow-Schritt '{typ.name}' für Mandant '{mandant.name}' aktiviert",
    )
    db.commit()
    db.refresh(schritt)
    return schritt
