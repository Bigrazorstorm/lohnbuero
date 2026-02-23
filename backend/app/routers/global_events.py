"""
Global Events API - Verwaltet globale Events wie Jahreswechsel, Mindestlohnerhöhung, etc.
Diese Events fügen automatisch zusätzliche Workflow-Schritte für betroffene Mandanten hinzu.
"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin, require_admin_or_teamleitung
from app.database import get_db
from app.models import (
    GlobalEvent, GlobalEventSchritt, User, GlobalEventTyp,
    BranchenWorkflowSchritt, Branche, Tenant, Abrechnungsfirma
)
from app.schemas import (
    GlobalEventCreate, GlobalEventOut, GlobalEventUpdate,
    GlobalEventSchrittCreate, GlobalEventSchrittOut, GlobalEventSchrittUpdate,
    BranchenWorkflowSchrittCreate, BranchenWorkflowSchrittOut, BranchenWorkflowSchrittUpdate,
    TenantCreate, TenantOut, TenantUpdate,
    AbrechnungsfirmaCreate, AbrechnungsfirmaOut, AbrechnungsfirmaUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin-global-events"])


# ═══════════════════════════════════════════
# Tenant CRUD (Multi-Tenancy)
# ═══════════════════════════════════════════

@router.get("/tenants", response_model=List[TenantOut])
def list_tenants(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Listet alle Tenants auf."""
    q = db.query(Tenant)
    if not include_inactive:
        q = q.filter(Tenant.ist_aktiv == True)
    return q.order_by(Tenant.name).all()


@router.post("/tenants", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(
    data: TenantCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Erstellt einen neuen Tenant."""
    existing = db.query(Tenant).filter(
        (Tenant.name == data.name) | (Tenant.code == data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant mit diesem Namen/Code existiert bereits")

    tenant = Tenant(**data.model_dump())
    db.add(tenant)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="tenant",
        objekt_id=tenant.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": tenant.name, "code": tenant.code},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Tenant '{tenant.name}' erstellt",
    )
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/tenants/{tenant_id}", response_model=TenantOut)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant nicht gefunden")
    return tenant


@router.patch("/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(tenant, k) for k in update_data}
    
    for key, value in update_data.items():
        setattr(tenant, key, value)

    audit_service.log(
        db,
        objekt_typ="tenant",
        objekt_id=tenant.id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Tenant '{tenant.name}' aktualisiert",
    )
    db.commit()
    db.refresh(tenant)
    return tenant


# ═══════════════════════════════════════════
# Abrechnungsfirma CRUD
# ═══════════════════════════════════════════

@router.get("/tenants/{tenant_id}/abrechnungsfirmen", response_model=List[AbrechnungsfirmaOut])
def list_abrechnungsfirmen(
    tenant_id: int,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Listet alle Abrechnungsfirmen eines Tenants auf."""
    q = db.query(Abrechnungsfirma).filter(Abrechnungsfirma.tenant_id == tenant_id)
    if not include_inactive:
        q = q.filter(Abrechnungsfirma.ist_aktiv == True)
    return q.order_by(Abrechnungsfirma.name).all()


@router.post("/abrechnungsfirmen", response_model=AbrechnungsfirmaOut, status_code=status.HTTP_201_CREATED)
def create_abrechnungsfirma(
    data: AbrechnungsfirmaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Erstellt eine neue Abrechnungsfirma."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant nicht gefunden")
    
    # Check unique code within tenant
    existing = db.query(Abrechnungsfirma).filter(
        Abrechnungsfirma.tenant_id == data.tenant_id,
        Abrechnungsfirma.code == data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Code bereits vergeben in diesem Tenant")

    firma = Abrechnungsfirma(**data.model_dump())
    db.add(firma)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="abrechnungsfirma",
        objekt_id=firma.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": firma.name, "code": firma.code, "tenant_id": firma.tenant_id},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Abrechnungsfirma '{firma.name}' erstellt",
    )
    db.commit()
    db.refresh(firma)
    return firma


@router.patch("/abrechnungsfirmen/{firma_id}", response_model=AbrechnungsfirmaOut)
def update_abrechnungsfirma(
    firma_id: int,
    data: AbrechnungsfirmaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    firma = db.query(Abrechnungsfirma).filter(Abrechnungsfirma.id == firma_id).first()
    if not firma:
        raise HTTPException(status_code=404, detail="Abrechnungsfirma nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(firma, k) for k in update_data}
    
    for key, value in update_data.items():
        setattr(firma, key, value)

    audit_service.log(
        db,
        objekt_typ="abrechnungsfirma",
        objekt_id=firma.id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Abrechnungsfirma '{firma.name}' aktualisiert",
    )
    db.commit()
    db.refresh(firma)
    return firma


# ═══════════════════════════════════════════
# Global Events CRUD
# ═══════════════════════════════════════════

@router.get("/global-events", response_model=List[GlobalEventOut])
def list_global_events(
    include_inactive: bool = Query(False),
    include_abgeschlossen: bool = Query(False),
    typ: Optional[GlobalEventTyp] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Listet alle globalen Events auf."""
    q = db.query(GlobalEvent)
    if not include_inactive:
        q = q.filter(GlobalEvent.ist_aktiv == True)
    if not include_abgeschlossen:
        q = q.filter(GlobalEvent.ist_abgeschlossen == False)
    if typ:
        q = q.filter(GlobalEvent.typ == typ)
    return q.order_by(GlobalEvent.gueltig_von.desc()).all()


@router.post("/global-events", response_model=GlobalEventOut, status_code=status.HTTP_201_CREATED)
def create_global_event(
    data: GlobalEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Erstellt ein neues globales Event (z.B. Jahreswechsel 2026/2027).
    Dieses Event fügt automatisch zusätzliche Workflow-Schritte für alle betroffenen Mandanten hinzu.
    """
    event_data = data.model_dump(exclude={"schritte"})
    event = GlobalEvent(**event_data, erstellt_von_id=current_user.id)
    db.add(event)
    db.flush()
    
    # Add steps
    for idx, schritt_data in enumerate(data.schritte, start=1):
        schritt = GlobalEventSchritt(
            event_id=event.id,
            position=schritt_data.position or idx,
            **schritt_data.model_dump(exclude={"position"})
        )
        db.add(schritt)
    
    audit_service.log(
        db,
        objekt_typ="global_event",
        objekt_id=event.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": event.name, "typ": event.typ.value, "schritte_anzahl": len(data.schritte)},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Globales Event '{event.name}' erstellt mit {len(data.schritte)} Schritten",
    )
    db.commit()
    db.refresh(event)
    return event


@router.get("/global-events/{event_id}", response_model=GlobalEventOut)
def get_global_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    event = db.query(GlobalEvent).filter(GlobalEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    return event


@router.patch("/global-events/{event_id}", response_model=GlobalEventOut)
def update_global_event(
    event_id: int,
    data: GlobalEventUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    event = db.query(GlobalEvent).filter(GlobalEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(event, k) for k in update_data}
    
    for key, value in update_data.items():
        setattr(event, key, value)

    audit_service.log(
        db,
        objekt_typ="global_event",
        objekt_id=event.id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Globales Event '{event.name}' aktualisiert",
    )
    db.commit()
    db.refresh(event)
    return event


@router.delete("/global-events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_event(
    event_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Löscht ein globales Event (Soft-Delete via ist_aktiv=False)."""
    event = db.query(GlobalEvent).filter(GlobalEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    
    event.ist_aktiv = False
    
    audit_service.log(
        db,
        objekt_typ="global_event",
        objekt_id=event.id,
        aktionstyp="geloescht",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Globales Event '{event.name}' deaktiviert",
    )
    db.commit()


# ═══════════════════════════════════════════
# Global Event Schritte CRUD
# ═══════════════════════════════════════════

@router.post("/global-events/{event_id}/schritte", response_model=GlobalEventSchrittOut, status_code=status.HTTP_201_CREATED)
def add_global_event_schritt(
    event_id: int,
    data: GlobalEventSchrittCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Fügt einen neuen Schritt zu einem globalen Event hinzu."""
    event = db.query(GlobalEvent).filter(GlobalEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    
    schritt = GlobalEventSchritt(event_id=event_id, **data.model_dump())
    db.add(schritt)
    db.flush()
    
    audit_service.log(
        db,
        objekt_typ="global_event_schritt",
        objekt_id=schritt.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"titel": schritt.titel, "event_id": event_id},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Schritt '{schritt.titel}' zu Event '{event.name}' hinzugefügt",
    )
    db.commit()
    db.refresh(schritt)
    return schritt


@router.patch("/global-events/schritte/{schritt_id}", response_model=GlobalEventSchrittOut)
def update_global_event_schritt(
    schritt_id: int,
    data: GlobalEventSchrittUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    schritt = db.query(GlobalEventSchritt).filter(GlobalEventSchritt.id == schritt_id).first()
    if not schritt:
        raise HTTPException(status_code=404, detail="Schritt nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(schritt, k) for k in update_data}
    
    for key, value in update_data.items():
        setattr(schritt, key, value)

    audit_service.log(
        db,
        objekt_typ="global_event_schritt",
        objekt_id=schritt.id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Schritt '{schritt.titel}' aktualisiert",
    )
    db.commit()
    db.refresh(schritt)
    return schritt


@router.delete("/global-events/schritte/{schritt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_event_schritt(
    schritt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    schritt = db.query(GlobalEventSchritt).filter(GlobalEventSchritt.id == schritt_id).first()
    if not schritt:
        raise HTTPException(status_code=404, detail="Schritt nicht gefunden")
    
    schritt.ist_aktiv = False
    
    audit_service.log(
        db,
        objekt_typ="global_event_schritt",
        objekt_id=schritt.id,
        aktionstyp="geloescht",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Schritt '{schritt.titel}' deaktiviert",
    )
    db.commit()


# ═══════════════════════════════════════════
# Branchenspezifische Workflow-Schritte CRUD
# ═══════════════════════════════════════════

@router.get("/branchen/{branche_id}/workflow-schritte", response_model=List[BranchenWorkflowSchrittOut])
def list_branchen_workflow_schritte(
    branche_id: int,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Listet alle branchenspezifischen Workflow-Schritte einer Branche auf."""
    branche = db.query(Branche).filter(Branche.id == branche_id).first()
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")
    
    q = db.query(BranchenWorkflowSchritt).filter(BranchenWorkflowSchritt.branche_id == branche_id)
    if not include_inactive:
        q = q.filter(BranchenWorkflowSchritt.ist_aktiv == True)
    return q.order_by(BranchenWorkflowSchritt.position).all()


@router.post("/branchen-workflow-schritte", response_model=BranchenWorkflowSchrittOut, status_code=status.HTTP_201_CREATED)
def create_branchen_workflow_schritt(
    data: BranchenWorkflowSchrittCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Erstellt einen branchenspezifischen Workflow-Schritt.
    Dieser wird automatisch in alle Workflows von Mandanten dieser Branche eingefügt.
    """
    branche = db.query(Branche).filter(Branche.id == data.branche_id).first()
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")
    
    schritt = BranchenWorkflowSchritt(**data.model_dump())
    db.add(schritt)
    db.flush()
    
    audit_service.log(
        db,
        objekt_typ="branchen_workflow_schritt",
        objekt_id=schritt.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"titel": schritt.titel, "branche_id": data.branche_id, "branche": branche.name},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Branchenspezifischer Schritt '{schritt.titel}' für '{branche.name}' erstellt",
    )
    db.commit()
    db.refresh(schritt)
    return schritt


@router.patch("/branchen-workflow-schritte/{schritt_id}", response_model=BranchenWorkflowSchrittOut)
def update_branchen_workflow_schritt(
    schritt_id: int,
    data: BranchenWorkflowSchrittUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    schritt = db.query(BranchenWorkflowSchritt).filter(BranchenWorkflowSchritt.id == schritt_id).first()
    if not schritt:
        raise HTTPException(status_code=404, detail="Schritt nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(schritt, k) for k in update_data}
    
    for key, value in update_data.items():
        setattr(schritt, key, value)

    audit_service.log(
        db,
        objekt_typ="branchen_workflow_schritt",
        objekt_id=schritt.id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Branchenspezifischer Schritt '{schritt.titel}' aktualisiert",
    )
    db.commit()
    db.refresh(schritt)
    return schritt


@router.delete("/branchen-workflow-schritte/{schritt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branchen_workflow_schritt(
    schritt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    schritt = db.query(BranchenWorkflowSchritt).filter(BranchenWorkflowSchritt.id == schritt_id).first()
    if not schritt:
        raise HTTPException(status_code=404, detail="Schritt nicht gefunden")
    
    schritt.ist_aktiv = False
    
    audit_service.log(
        db,
        objekt_typ="branchen_workflow_schritt",
        objekt_id=schritt.id,
        aktionstyp="geloescht",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Branchenspezifischer Schritt '{schritt.titel}' deaktiviert",
    )
    db.commit()


# ═══════════════════════════════════════════
# Event-Typen Übersicht
# ═══════════════════════════════════════════

@router.get("/global-event-typen")
def list_global_event_typen(
    _: User = Depends(require_admin_or_teamleitung),
):
    """Gibt alle verfügbaren Event-Typen zurück."""
    return [
        {"value": typ.value, "label": typ.value.replace("_", " ").title()}
        for typ in GlobalEventTyp
    ]
