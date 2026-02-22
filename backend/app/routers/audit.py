"""Audit log – read-only endpoints with filtering and CSV export."""
import csv
import io
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin_or_teamleitung
from app.database import get_db
from app.models import AuditLog, User
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/", response_model=List[AuditLogOut])
def list_audit(
    mandant_id: Optional[int] = Query(None),
    objekt_typ: Optional[str] = Query(None),
    aktionstyp: Optional[str] = Query(None),
    benutzer_id: Optional[int] = Query(None),
    monat: Optional[int] = Query(None),
    jahr: Optional[int] = Query(None),
    von: Optional[datetime] = Query(None),
    bis: Optional[datetime] = Query(None),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    q = db.query(AuditLog)
    if mandant_id:
        q = q.filter(AuditLog.mandant_id == mandant_id)
    if objekt_typ:
        q = q.filter(AuditLog.objekt_typ == objekt_typ)
    if aktionstyp:
        q = q.filter(AuditLog.aktionstyp == aktionstyp)
    if benutzer_id:
        q = q.filter(AuditLog.benutzer_id == benutzer_id)
    if monat:
        q = q.filter(AuditLog.monat == monat)
    if jahr:
        q = q.filter(AuditLog.jahr == jahr)
    if von:
        q = q.filter(AuditLog.zeitstempel >= von)
    if bis:
        q = q.filter(AuditLog.zeitstempel <= bis)
    q = q.order_by(AuditLog.zeitstempel.desc())
    return q.offset(offset).limit(limit).all()


@router.get("/export/csv")
def export_csv(
    mandant_id: Optional[int] = Query(None),
    objekt_typ: Optional[str] = Query(None),
    aktionstyp: Optional[str] = Query(None),
    monat: Optional[int] = Query(None),
    jahr: Optional[int] = Query(None),
    von: Optional[datetime] = Query(None),
    bis: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    q = db.query(AuditLog)
    if mandant_id:
        q = q.filter(AuditLog.mandant_id == mandant_id)
    if objekt_typ:
        q = q.filter(AuditLog.objekt_typ == objekt_typ)
    if aktionstyp:
        q = q.filter(AuditLog.aktionstyp == aktionstyp)
    if monat:
        q = q.filter(AuditLog.monat == monat)
    if jahr:
        q = q.filter(AuditLog.jahr == jahr)
    if von:
        q = q.filter(AuditLog.zeitstempel >= von)
    if bis:
        q = q.filter(AuditLog.zeitstempel <= bis)
    entries = q.order_by(AuditLog.zeitstempel.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Zeitstempel (UTC)", "Objekt-Typ", "Objekt-ID", "Mandant-ID",
        "Monat", "Jahr", "Aktionstyp", "Alter Wert", "Neuer Wert",
        "Benutzer-ID", "Benutzerrolle", "IP-Adresse", "Beschreibung",
    ])
    for e in entries:
        writer.writerow([
            e.id,
            e.zeitstempel.isoformat() if e.zeitstempel else "",
            e.objekt_typ,
            e.objekt_id or "",
            e.mandant_id or "",
            e.monat or "",
            e.jahr or "",
            e.aktionstyp,
            e.alter_wert or "",
            e.neuer_wert or "",
            e.benutzer_id or "",
            e.benutzerrolle or "",
            e.ip_adresse or "",
            e.beschreibung or "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-log.csv"},
    )
