from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import Mandant, MandantKategorie, User
from app.schemas import MandantCreate, MandantOut, MandantUpdate

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

    # Mandant portal users only see their own client
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
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    if data.nummer:
        existing = db.query(Mandant).filter(Mandant.nummer == data.nummer).first()
        if existing:
            raise HTTPException(status_code=400, detail="Mandantennummer bereits vorhanden")

    mandant = Mandant(**data.model_dump())
    db.add(mandant)
    db.commit()
    db.refresh(mandant)
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
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(mandant, k, v)

    db.commit()
    db.refresh(mandant)
    return mandant


@router.delete("/{mandant_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_mandant(
    mandant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")
    mandant.ist_aktiv = False
    db.commit()
