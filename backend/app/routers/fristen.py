"""Fristen-Vorlagen & deadline calculation endpoints."""
import json
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import (
    FristenVorlage, Fristenprofil, Fristenregel, Mandant, User,
)
from app.schemas import FristenVorlageOut, FristenprofilOut
from app.bankarbeitstage import berechne_frist

router = APIRouter(prefix="/api/fristen", tags=["fristen"])


# ─── Fristen-Vorlagen (Default Templates) ─────────────────────

@router.get("/vorlagen", response_model=List[FristenVorlageOut])
def list_fristen_vorlagen(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """List all available default deadline templates."""
    return db.query(FristenVorlage).filter(FristenVorlage.ist_aktiv == True).order_by(FristenVorlage.code).all()


@router.post("/{mandant_id}/apply-defaults", response_model=FristenprofilOut)
def apply_default_fristen(
    mandant_id: int,
    codes: List[str] = Query(None, description="List of FristenVorlage codes to apply. None = all applicable."),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    """Create or update a Fristenprofil for a mandant using default templates.

    Only applies templates that match the mandant's profile (e.g., SOKA only if SOKA-relevant).
    """
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    # Determine which defaults to apply
    vorlagen = db.query(FristenVorlage).filter(FristenVorlage.ist_aktiv == True).all()
    if codes:
        vorlagen = [v for v in vorlagen if v.code in codes]

    # Filter by branchenfilter
    is_soka = any(b.soka_relevant for b in mandant.branchen_liste) if mandant.branchen_liste else False
    applicable = []
    for v in vorlagen:
        if v.branchenfilter == "SOKA" and not is_soka:
            continue
        applicable.append(v)

    # Create or get profil
    profil = mandant.fristenprofil
    if not profil:
        profil = Fristenprofil(mandant_id=mandant_id, name=f"Fristenprofil {mandant.name}")
        db.add(profil)
        db.flush()
        mandant.fristenprofil_id = profil.id

    # Add rules from templates (skip duplicates)
    existing_fristarten = {r.fristart for r in profil.regeln}
    position = max((r.position for r in profil.regeln), default=0)

    for v in applicable:
        if v.code in existing_fristarten:
            continue
        position += 1
        regel = Fristenregel(
            profil_id=profil.id,
            position=position,
            fristart=v.code,
            regeltyp=v.regeltyp,
            regel_config=v.regel_config,
            interne_vorfrist_tage=v.default_interne_vorfrist_tage,
            ist_aktiv=True,
        )
        db.add(regel)

    audit_service.log(
        db,
        objekt_typ="fristenprofil",
        objekt_id=profil.id,
        mandant_id=mandant_id,
        aktionstyp="defaults_angewendet",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"applied_codes": [v.code for v in applicable]},
        ip_adresse=request.client.host if request and request.client else None,
        beschreibung=f"Default-Fristen auf Mandant '{mandant.name}' angewendet",
    )
    db.commit()
    db.refresh(profil)
    return profil


@router.get("/{mandant_id}/berechne")
def berechne_mandant_fristen(
    mandant_id: int,
    monat: int = Query(..., ge=1, le=12),
    jahr: int = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Calculate all deadline dates for a mandant in a specific month."""
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    profil = mandant.fristenprofil
    if not profil:
        return {"fristen": [], "message": "Kein Fristenprofil vorhanden"}

    ergebnisse = []
    for regel in profil.regeln:
        if not regel.ist_aktiv:
            continue

        config = json.loads(regel.regel_config)
        bundesland = regel.bundesland

        stichtag = berechne_frist(jahr, monat, regel.regeltyp.value, config, bundesland)

        # Calculate internal pre-deadline
        interne_vorfrist = None
        if stichtag and regel.interne_vorfrist_tage > 0:
            from app.bankarbeitstage import berechne_frist_relativ
            interne_vorfrist = berechne_frist_relativ(
                stichtag, -regel.interne_vorfrist_tage, bundesland
            )

        # Determine traffic-light status
        heute = date.today()
        ampel = "gruen"
        if stichtag:
            if heute > stichtag:
                ampel = "rot"
            elif interne_vorfrist and heute >= interne_vorfrist:
                ampel = "gelb"

        # Get FristenVorlage name for display
        vorlage = db.query(FristenVorlage).filter(FristenVorlage.code == regel.fristart).first()
        name = vorlage.name if vorlage else regel.fristart

        ergebnisse.append({
            "fristart": regel.fristart,
            "name": name,
            "externer_stichtag": stichtag.isoformat() if stichtag else None,
            "interne_vorfrist": interne_vorfrist.isoformat() if interne_vorfrist else None,
            "ampel": ampel,
            "regeltyp": regel.regeltyp.value,
            "ist_aktiv": regel.ist_aktiv,
        })

    return {"mandant_id": mandant_id, "monat": monat, "jahr": jahr, "fristen": ergebnisse}
