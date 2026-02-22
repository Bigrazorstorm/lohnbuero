from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import Mandant, MandantKategorie, User, MandantAenderung
from app.schemas import MandantCreate, MandantOut, MandantUpdate, MandantAenderungOut

router = APIRouter(prefix="/api/mandanten", tags=["mandanten"])


@router.get("/", response_model=List[MandantOut])
def list_mandanten(
    aktiv: Optional[bool] = Query(None),
    kategorie: Optional[MandantKategorie] = Query(None),
    sachbearbeiter_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    q = db.query(Mandant)

    from app.models import UserRole
    if current_user.role == UserRole.MANDANT:
        q = q.filter(Mandant.portal_user_id == current_user.id)
    else:
        if aktiv is not None:
            q = q.filter(Mandant.ist_aktiv == aktiv)
        if kategorie:
            q = q.filter(Mandant.kategorie == kategorie)
        if sachbearbeiter_id:
            q = q.filter(Mandant.sachbearbeiter_id == sachbearbeiter_id)

    return q.order_by(Mandant.name).all()


@router.post("/", response_model=MandantOut, status_code=status.HTTP_201_CREATED)
def create_mandant(
    data: MandantCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    if data.nummer:
        existing = db.query(Mandant).filter(Mandant.nummer == data.nummer).first()
        if existing:
            raise HTTPException(status_code=400, detail="Mandantennummer bereits vorhanden")

    mandant = Mandant(**data.model_dump())
    db.add(mandant)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="mandant",
        objekt_id=mandant.id,
        mandant_id=mandant.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": mandant.name, "nummer": mandant.nummer, "kategorie": mandant.kategorie},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Mandant '{mandant.name}' angelegt",
    )
    db.commit()
    db.refresh(mandant)

    # Trigger onboarding email sequence (best-effort)
    try:
        from app.routers.email_templates import send_onboarding_emails
        send_onboarding_emails(db, mandant)
        db.commit()
    except Exception:
        pass

    return mandant


@router.get("/{mandant_id}", response_model=MandantOut)
def get_mandant(
    mandant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    from app.models import UserRole
    if current_user.role == UserRole.MANDANT and mandant.portal_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    return mandant


@router.patch("/{mandant_id}", response_model=MandantOut)
def update_mandant(
    mandant_id: int,
    data: MandantUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    from app.models import MandantAenderung
    import json

    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    aenderung_zum = update_data.pop('aenderung_zum', None)

    if aenderung_zum is not None:
        # Geplante Änderung erstellen
        aenderung = MandantAenderung(
            mandant_id=mandant_id,
            aenderung_zum=aenderung_zum,
            aenderungen=json.dumps(update_data),
            erstellt_von_id=current_user.id
        )
        db.add(aenderung)
        db.flush()  # Get the ID

        audit_service.log(
            db,
            objekt_typ="mandant_aenderung",
            objekt_id=aenderung.id,
            mandant_id=mandant_id,
            aktionstyp="geplante_aenderung_erstellt",
            benutzer_id=current_user.id,
            benutzerrolle=current_user.role.value,
            neuer_wert={"aenderung_zum": aenderung_zum.isoformat(), "aenderungen": update_data},
            ip_adresse=request.client.host if request.client else None,
            beschreibung=f"Geplante Änderung für Mandant '{mandant.name}' erstellt",
        )
    else:
        # Sofortige Änderung
        old_vals = {k: getattr(mandant, k) for k in update_data}

        for k, v in update_data.items():
            setattr(mandant, k, v)

        audit_service.log(
            db,
            objekt_typ="mandant",
            objekt_id=mandant.id,
            mandant_id=mandant.id,
            aktionstyp="stammdaten_geaendert",
            benutzer_id=current_user.id,
            benutzerrolle=current_user.role.value,
            alter_wert=old_vals,
            neuer_wert=update_data,
            ip_adresse=request.client.host if request.client else None,
            beschreibung=f"Stammdaten von Mandant '{mandant.name}' geändert",
        )

    db.commit()
    db.refresh(mandant)
    return mandant


@router.delete("/{mandant_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_mandant(
    mandant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    old_aktiv = mandant.ist_aktiv
    mandant.ist_aktiv = False

    audit_service.log(
        db,
        objekt_typ="mandant",
        objekt_id=mandant.id,
        mandant_id=mandant.id,
        aktionstyp="archiviert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"ist_aktiv": old_aktiv},
        neuer_wert={"ist_aktiv": False},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Mandant '{mandant.name}' archiviert",
    )
    db.commit()


# ─────────────────────────────────────────
# Mandant Änderungen
# ─────────────────────────────────────────

@router.get("/{mandant_id}/aenderungen", response_model=List[MandantAenderungOut])
def list_mandant_aenderungen(
    mandant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    return db.query(MandantAenderung).filter(MandantAenderung.mandant_id == mandant_id).order_by(MandantAenderung.erstellt_am).all()


@router.patch("/{mandant_id}/aenderungen/{aenderung_id}/abbruch")
def cancel_mandant_aenderung(
    mandant_id: int,
    aenderung_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    aenderung = db.query(MandantAenderung).filter(
        MandantAenderung.id == aenderung_id,
        MandantAenderung.mandant_id == mandant_id
    ).first()
    if not aenderung:
        raise HTTPException(status_code=404, detail="Änderung nicht gefunden")

    if aenderung.status != "geplant":
        raise HTTPException(status_code=400, detail="Änderung kann nicht abgebrochen werden")

    aenderung.status = "abgebrochen"
    aenderung.abgebrochen_am = datetime.utcnow()
    aenderung.abgebrochen_von_id = current_user.id

    audit_service.log(
        db,
        objekt_typ="mandant_aenderung",
        objekt_id=aenderung.id,
        mandant_id=mandant_id,
        aktionstyp="geplante_aenderung_abgebrochen",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"status": "geplant"},
        neuer_wert={"status": "abgebrochen"},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Geplante Änderung für Mandant abgebrochen",
    )
    db.commit()
    return {"message": "Änderung abgebrochen"}
