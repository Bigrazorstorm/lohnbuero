from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, get_password_hash, require_admin, require_staff
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    return db.query(User).all()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-Mail bereits vergeben")
    user = User(
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        is_active=data.is_active,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="user",
        objekt_id=user.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"email": user.email, "full_name": user.full_name, "role": user.role.value},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Benutzer '{user.full_name}' angelegt",
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old_vals = {k: getattr(user, k) for k in update_data if k != "password"}

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for k, v in update_data.items():
        setattr(user, k, v)

    audit_service.log(
        db,
        objekt_typ="user",
        objekt_id=user.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old_vals,
        neuer_wert={k: v for k, v in update_data.items() if k != "hashed_password"},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Benutzer '{user.full_name}' aktualisiert",
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/archivieren", response_model=UserOut)
def archiviere_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Archive a user: deactivate login while preserving history."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Eigenen Account kann nicht archiviert werden")

    user.is_active = False
    user.is_archived = True

    audit_service.log(
        db,
        objekt_typ="user",
        objekt_id=user.id,
        aktionstyp="archiviert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"is_active": False, "is_archived": True},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Benutzer '{user.full_name}' archiviert (Login deaktiviert, Historie bleibt)",
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/anonymisieren", response_model=UserOut)
def anonymisiere_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Anonymize a user for DSGVO compliance. Replaces personal data with anonymous values."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Eigenen Account kann nicht anonymisiert werden")

    if user.anonymisiert_am:
        raise HTTPException(status_code=400, detail="Benutzer bereits anonymisiert")

    old_name = user.full_name
    old_email = user.email

    # Anonymize personal data
    anon_id = f"anon_{user.id}"
    user.full_name = f"Anonymisiert ({anon_id})"
    user.email = f"{anon_id}@anonymisiert.local"
    user.hashed_password = "ANONYMIZED"
    user.is_active = False
    user.is_archived = True
    user.anonymisiert_am = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="user",
        objekt_id=user.id,
        aktionstyp="anonymisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert={"full_name": old_name, "email": old_email},
        neuer_wert={"full_name": user.full_name, "email": user.email, "anonymisiert_am": user.anonymisiert_am.isoformat()},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Benutzer anonymisiert (DSGVO). Ehemals: {old_name}",
    )
    db.commit()
    db.refresh(user)
    return user
