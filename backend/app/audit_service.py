"""Audit service – central helper to create AuditLog entries.

All audit entries are append-only (no UPDATE/DELETE ever issued on audit_logs).
"""
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLog


def log(
    db: Session,
    *,
    objekt_typ: str,
    objekt_id: Optional[int],
    aktionstyp: str,
    benutzer_id: Optional[int] = None,
    benutzerrolle: Optional[str] = None,
    mandant_id: Optional[int] = None,
    monat: Optional[int] = None,
    jahr: Optional[int] = None,
    alter_wert: Any = None,
    neuer_wert: Any = None,
    ip_adresse: Optional[str] = None,
    beschreibung: Optional[str] = None,
) -> AuditLog:
    """Create and persist a single audit log entry."""
    entry = AuditLog(
        objekt_typ=objekt_typ,
        objekt_id=objekt_id,
        mandant_id=mandant_id,
        monat=monat,
        jahr=jahr,
        aktionstyp=aktionstyp,
        alter_wert=json.dumps(alter_wert, default=str) if alter_wert is not None else None,
        neuer_wert=json.dumps(neuer_wert, default=str) if neuer_wert is not None else None,
        benutzer_id=benutzer_id,
        benutzerrolle=benutzerrolle,
        zeitstempel=datetime.utcnow(),
        ip_adresse=ip_adresse,
        beschreibung=beschreibung,
    )
    db.add(entry)
    # Do NOT commit here; let the calling transaction commit everything atomically.
    return entry
