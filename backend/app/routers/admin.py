"""Admin Stammdaten-Pflege: Branchen, Ausgabewege, SMTP/IMAP, Defaults, Upload-Config."""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin, require_admin_or_teamleitung
from app.database import get_db
from app.models import (
    AusgabewegConfig, Branche, ImapKonfiguration, SmtpKonfiguration,
    SystemDefault, UploadKonfiguration, User,
)
from app.schemas import (
    AusgabewegConfigCreate, AusgabewegConfigOut, AusgabewegConfigUpdate,
    BrancheCreate, BrancheOut, BrancheUpdate,
    ImapKonfigurationCreate, ImapKonfigurationOut, ImapKonfigurationUpdate,
    SmtpKonfigurationCreate, SmtpKonfigurationOut, SmtpKonfigurationUpdate,
    SystemDefaultOut,
    UploadKonfigurationOut, UploadKonfigurationUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ═══════════════════════════════════════════
# Branchen CRUD
# ═══════════════════════════════════════════

@router.get("/branchen", response_model=List[BrancheOut])
def list_branchen(
    include_archiviert: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    q = db.query(Branche)
    if not include_archiviert:
        q = q.filter(Branche.ist_archiviert == False)
    return q.order_by(Branche.name).all()


@router.post("/branchen", response_model=BrancheOut, status_code=status.HTTP_201_CREATED)
def create_branche(
    data: BrancheCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.query(Branche).filter(Branche.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Branche mit diesem Namen existiert bereits")

    branche = Branche(**data.model_dump())
    db.add(branche)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="branche",
        objekt_id=branche.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": branche.name, "faktor": branche.faktor},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Branche '{branche.name}' erstellt",
    )
    db.commit()
    db.refresh(branche)
    return branche


@router.get("/branchen/{branche_id}", response_model=BrancheOut)
def get_branche(
    branche_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    branche = db.query(Branche).filter(Branche.id == branche_id).first()
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")
    return branche


@router.patch("/branchen/{branche_id}", response_model=BrancheOut)
def update_branche(
    branche_id: int,
    data: BrancheUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    branche = db.query(Branche).filter(Branche.id == branche_id).first()
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(branche, k) for k in update_data}

    for k, v in update_data.items():
        setattr(branche, k, v)
    branche.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="branche",
        objekt_id=branche.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Branche '{branche.name}' geändert",
    )
    db.commit()
    db.refresh(branche)
    return branche


@router.delete("/branchen/{branche_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_branche(
    branche_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    branche = db.query(Branche).filter(Branche.id == branche_id).first()
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")
    branche.ist_archiviert = True
    branche.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="branche",
        objekt_id=branche.id,
        aktionstyp="archiviert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Branche '{branche.name}' archiviert",
    )
    db.commit()


# ═══════════════════════════════════════════
# Ausgabewege CRUD
# ═══════════════════════════════════════════

@router.get("/ausgabewege", response_model=List[AusgabewegConfigOut])
def list_ausgabewege(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    return db.query(AusgabewegConfig).order_by(AusgabewegConfig.name).all()


@router.post("/ausgabewege", response_model=AusgabewegConfigOut, status_code=status.HTTP_201_CREATED)
def create_ausgabeweg(
    data: AusgabewegConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.query(AusgabewegConfig).filter(AusgabewegConfig.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ausgabeweg mit diesem Namen existiert bereits")

    ausgabeweg = AusgabewegConfig(**data.model_dump())
    db.add(ausgabeweg)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="ausgabeweg",
        objekt_id=ausgabeweg.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": ausgabeweg.name},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Ausgabeweg '{ausgabeweg.name}' erstellt",
    )
    db.commit()
    db.refresh(ausgabeweg)
    return ausgabeweg


@router.get("/ausgabewege/{ausgabeweg_id}", response_model=AusgabewegConfigOut)
def get_ausgabeweg(
    ausgabeweg_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    ausgabeweg = db.query(AusgabewegConfig).filter(AusgabewegConfig.id == ausgabeweg_id).first()
    if not ausgabeweg:
        raise HTTPException(status_code=404, detail="Ausgabeweg nicht gefunden")
    return ausgabeweg


@router.patch("/ausgabewege/{ausgabeweg_id}", response_model=AusgabewegConfigOut)
def update_ausgabeweg(
    ausgabeweg_id: int,
    data: AusgabewegConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    ausgabeweg = db.query(AusgabewegConfig).filter(AusgabewegConfig.id == ausgabeweg_id).first()
    if not ausgabeweg:
        raise HTTPException(status_code=404, detail="Ausgabeweg nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(ausgabeweg, k) for k in update_data}

    for k, v in update_data.items():
        setattr(ausgabeweg, k, v)
    ausgabeweg.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="ausgabeweg",
        objekt_id=ausgabeweg.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Ausgabeweg '{ausgabeweg.name}' geändert",
    )
    db.commit()
    db.refresh(ausgabeweg)
    return ausgabeweg


@router.delete("/ausgabewege/{ausgabeweg_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_ausgabeweg(
    ausgabeweg_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    ausgabeweg = db.query(AusgabewegConfig).filter(AusgabewegConfig.id == ausgabeweg_id).first()
    if not ausgabeweg:
        raise HTTPException(status_code=404, detail="Ausgabeweg nicht gefunden")
    ausgabeweg.ist_aktiv = False
    ausgabeweg.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="ausgabeweg",
        objekt_id=ausgabeweg.id,
        aktionstyp="deaktiviert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Ausgabeweg '{ausgabeweg.name}' deaktiviert",
    )
    db.commit()


# ═══════════════════════════════════════════
# SMTP-Konfiguration
# ═══════════════════════════════════════════

def _mask_password(password: str) -> str:
    """Return masked version of password for audit logging."""
    if not password:
        return ""
    return password[:2] + "***" + password[-1:] if len(password) > 3 else "***"


@router.get("/smtp", response_model=List[SmtpKonfigurationOut])
def list_smtp(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(SmtpKonfiguration).order_by(SmtpKonfiguration.id).all()


@router.post("/smtp", response_model=SmtpKonfigurationOut, status_code=status.HTTP_201_CREATED)
def create_smtp(
    data: SmtpKonfigurationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    smtp = SmtpKonfiguration(
        name=data.name,
        server=data.server,
        port=data.port,
        tls_ssl=data.tls_ssl,
        auth_user=data.auth_user,
        auth_password_encrypted=data.auth_password or "",
        absender_email=data.absender_email,
        reply_to=data.reply_to,
        ist_aktiv=data.ist_aktiv,
    )
    db.add(smtp)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="smtp_konfiguration",
        objekt_id=smtp.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"server": smtp.server, "port": smtp.port, "absender": smtp.absender_email},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"SMTP-Konfiguration '{smtp.name}' erstellt",
    )
    db.commit()
    db.refresh(smtp)
    return smtp


@router.patch("/smtp/{smtp_id}", response_model=SmtpKonfigurationOut)
def update_smtp(
    smtp_id: int,
    data: SmtpKonfigurationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    smtp = db.query(SmtpKonfiguration).filter(SmtpKonfiguration.id == smtp_id).first()
    if not smtp:
        raise HTTPException(status_code=404, detail="SMTP-Konfiguration nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    # Don't log password in audit
    audit_changes = {k: v for k, v in update_data.items() if k != "auth_password"}
    old = {k: getattr(smtp, k) for k in audit_changes}

    if "auth_password" in update_data:
        smtp.auth_password_encrypted = update_data.pop("auth_password") or ""
        audit_changes["auth_password"] = "(geändert)"

    for k, v in update_data.items():
        setattr(smtp, k, v)
    smtp.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="smtp_konfiguration",
        objekt_id=smtp.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=audit_changes,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"SMTP-Konfiguration '{smtp.name}' geändert",
    )
    db.commit()
    db.refresh(smtp)
    return smtp


@router.post("/smtp/{smtp_id}/test")
def test_smtp(
    smtp_id: int,
    empfaenger: str = Query(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Send a test email via the configured SMTP settings (simulated)."""
    smtp = db.query(SmtpKonfiguration).filter(SmtpKonfiguration.id == smtp_id).first()
    if not smtp:
        raise HTTPException(status_code=404, detail="SMTP-Konfiguration nicht gefunden")

    # In production, this would actually send an email.
    # For now, simulate success and log the attempt.
    audit_service.log(
        db,
        objekt_typ="smtp_konfiguration",
        objekt_id=smtp.id,
        aktionstyp="testmail",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"empfaenger": empfaenger, "server": smtp.server},
        ip_adresse=request.client.host if request and request.client else None,
        beschreibung=f"Test-E-Mail an {empfaenger} über '{smtp.name}' gesendet",
    )
    db.commit()

    return {
        "success": True,
        "message": f"Test-E-Mail an {empfaenger} wurde simuliert (SMTP: {smtp.server}:{smtp.port})",
    }


@router.delete("/smtp/{smtp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_smtp(
    smtp_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    smtp = db.query(SmtpKonfiguration).filter(SmtpKonfiguration.id == smtp_id).first()
    if not smtp:
        raise HTTPException(status_code=404, detail="SMTP-Konfiguration nicht gefunden")

    audit_service.log(
        db,
        objekt_typ="smtp_konfiguration",
        objekt_id=smtp.id,
        aktionstyp="geloescht",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"SMTP-Konfiguration '{smtp.name}' gelöscht",
    )
    db.delete(smtp)
    db.commit()


# ═══════════════════════════════════════════
# IMAP-Konfiguration
# ═══════════════════════════════════════════

@router.get("/imap", response_model=List[ImapKonfigurationOut])
def list_imap(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(ImapKonfiguration).order_by(ImapKonfiguration.id).all()


@router.post("/imap", response_model=ImapKonfigurationOut, status_code=status.HTTP_201_CREATED)
def create_imap(
    data: ImapKonfigurationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    imap = ImapKonfiguration(
        name=data.name,
        server=data.server,
        port=data.port,
        tls_ssl=data.tls_ssl,
        auth_user=data.auth_user,
        auth_password_encrypted=data.auth_password or "",
        postfach=data.postfach,
        ordner=data.ordner,
        polling_intervall_sekunden=data.polling_intervall_sekunden,
        zuordnung_methode=data.zuordnung_methode,
        ist_aktiv=data.ist_aktiv,
    )
    db.add(imap)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="imap_konfiguration",
        objekt_id=imap.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"server": imap.server, "port": imap.port, "postfach": imap.postfach},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"IMAP-Konfiguration '{imap.name}' erstellt",
    )
    db.commit()
    db.refresh(imap)
    return imap


@router.patch("/imap/{imap_id}", response_model=ImapKonfigurationOut)
def update_imap(
    imap_id: int,
    data: ImapKonfigurationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    imap = db.query(ImapKonfiguration).filter(ImapKonfiguration.id == imap_id).first()
    if not imap:
        raise HTTPException(status_code=404, detail="IMAP-Konfiguration nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    audit_changes = {k: v for k, v in update_data.items() if k != "auth_password"}
    old = {k: getattr(imap, k) for k in audit_changes}

    if "auth_password" in update_data:
        imap.auth_password_encrypted = update_data.pop("auth_password") or ""
        audit_changes["auth_password"] = "(geändert)"

    for k, v in update_data.items():
        setattr(imap, k, v)
    imap.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="imap_konfiguration",
        objekt_id=imap.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=audit_changes,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"IMAP-Konfiguration '{imap.name}' geändert",
    )
    db.commit()
    db.refresh(imap)
    return imap


@router.delete("/imap/{imap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imap(
    imap_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    imap = db.query(ImapKonfiguration).filter(ImapKonfiguration.id == imap_id).first()
    if not imap:
        raise HTTPException(status_code=404, detail="IMAP-Konfiguration nicht gefunden")

    audit_service.log(
        db,
        objekt_typ="imap_konfiguration",
        objekt_id=imap.id,
        aktionstyp="geloescht",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"IMAP-Konfiguration '{imap.name}' gelöscht",
    )
    db.delete(imap)
    db.commit()


# ═══════════════════════════════════════════
# System-Defaults
# ═══════════════════════════════════════════

@router.get("/defaults", response_model=List[SystemDefaultOut])
def list_defaults(
    bereich: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(SystemDefault)
    if bereich:
        q = q.filter(SystemDefault.bereich == bereich)
    return q.order_by(SystemDefault.bereich, SystemDefault.name).all()


@router.post("/defaults/reset/{bereich}")
def reset_defaults(
    bereich: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reset a specific default area to its initial configuration."""
    from app.seed_defaults import seed_defaults_for_bereich
    seed_defaults_for_bereich(db, bereich)

    audit_service.log(
        db,
        objekt_typ="system_default",
        objekt_id=None,
        aktionstyp="zurueckgesetzt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"bereich": bereich},
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"System-Defaults für Bereich '{bereich}' zurückgesetzt",
    )
    db.commit()
    return {"success": True, "message": f"Defaults für '{bereich}' zurückgesetzt"}


# ═══════════════════════════════════════════
# Upload-Konfiguration
# ═══════════════════════════════════════════

@router.get("/upload-config", response_model=UploadKonfigurationOut)
def get_upload_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = db.query(UploadKonfiguration).first()
    if not config:
        config = UploadKonfiguration()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.patch("/upload-config", response_model=UploadKonfigurationOut)
def update_upload_config(
    data: UploadKonfigurationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    config = db.query(UploadKonfiguration).first()
    if not config:
        config = UploadKonfiguration()
        db.add(config)
        db.flush()

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(config, k) for k in update_data}

    for k, v in update_data.items():
        setattr(config, k, v)
    config.updated_at = datetime.utcnow()

    audit_service.log(
        db,
        objekt_typ="upload_konfiguration",
        objekt_id=config.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung="Upload-Konfiguration geändert",
    )
    db.commit()
    db.refresh(config)
    return config
