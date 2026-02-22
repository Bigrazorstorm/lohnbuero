"""Reporting endpoints: Points per employee, drilldown, CSV export."""
import csv
import io
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import (
    Mandant, PunkteKonfiguration, Sonderaufgabe, SonderaufgabeStatus,
    User, UserRole, WorkflowInstanz, WorkflowItem, WorkflowStatus,
    ChecklistItemStatus,
)
from app.schemas import MandantPunkteDetail, MitarbeiterPunkteReport

router = APIRouter(prefix="/api/reporting", tags=["reporting"])


# ─── Points per Employee ──────────────────────────────────────

@router.get("/punkte/mitarbeiter", response_model=List[MitarbeiterPunkteReport])
def punkte_pro_mitarbeiter(
    monat: Optional[int] = Query(None, ge=1, le=12),
    jahr: Optional[int] = Query(None),
    quartal: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Points earned per employee for a given period."""
    users = db.query(User).filter(
        User.role.in_([UserRole.SACHBEARBEITER, UserRole.PRUEFER, UserRole.TEAMLEITUNG]),
        User.is_active == True,
    ).all()

    results = []
    for user in users:
        # Workflow points
        q_items = db.query(func.coalesce(func.sum(WorkflowItem.punkte), 0)).filter(
            WorkflowItem.erledigt_von_id == user.id,
            WorkflowItem.status == ChecklistItemStatus.ERLEDIGT,
        )

        # Sonderaufgaben points
        q_sonder = db.query(func.coalesce(func.sum(Sonderaufgabe.punkte), 0)).filter(
            Sonderaufgabe.verantwortlicher_id == user.id,
            Sonderaufgabe.status == SonderaufgabeStatus.ABGESCHLOSSEN,
        )

        # Mandanten count
        q_mandanten = db.query(func.count(Mandant.id)).filter(
            Mandant.sachbearbeiter_id == user.id,
            Mandant.ist_aktiv == True,
        )

        # Apply period filters
        if jahr:
            q_items = q_items.join(WorkflowInstanz, WorkflowItem.instanz_id == WorkflowInstanz.id)
            q_items = q_items.filter(WorkflowInstanz.jahr == jahr)
            q_sonder = q_sonder.filter(Sonderaufgabe.jahr == jahr)

            if monat:
                q_items = q_items.filter(WorkflowInstanz.monat == monat)
                q_sonder = q_sonder.filter(Sonderaufgabe.monat == monat)
            elif quartal:
                monate = _quartal_monate(quartal)
                q_items = q_items.filter(WorkflowInstanz.monat.in_(monate))
                q_sonder = q_sonder.filter(Sonderaufgabe.monat.in_(monate))

        wf_punkte = q_items.scalar() or 0.0
        so_punkte = q_sonder.scalar() or 0.0
        mandanten_count = q_mandanten.scalar() or 0

        results.append(MitarbeiterPunkteReport(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            punkte_gesamt=wf_punkte + so_punkte,
            punkte_workflows=wf_punkte,
            punkte_sonderaufgaben=so_punkte,
            mandanten_count=mandanten_count,
        ))

    results.sort(key=lambda x: x.punkte_gesamt, reverse=True)
    return results


# ─── Drilldown: Employee → Mandanten → Months ─────────────────

@router.get("/punkte/mitarbeiter/{user_id}/detail", response_model=List[MandantPunkteDetail])
def punkte_detail_mitarbeiter(
    user_id: int,
    jahr: int = Query(...),
    monat: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Drilldown: Points per mandant/month for a specific employee."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    # Find all workflow items this user completed
    q = (
        db.query(
            WorkflowInstanz.mandant_id,
            Mandant.name.label("mandant_name"),
            WorkflowInstanz.monat,
            WorkflowInstanz.jahr,
            func.coalesce(func.sum(WorkflowItem.punkte), 0).label("punkte"),
        )
        .join(WorkflowItem, WorkflowItem.instanz_id == WorkflowInstanz.id)
        .join(Mandant, Mandant.id == WorkflowInstanz.mandant_id)
        .filter(
            WorkflowItem.erledigt_von_id == user_id,
            WorkflowItem.status == ChecklistItemStatus.ERLEDIGT,
            WorkflowInstanz.jahr == jahr,
        )
    )

    if monat:
        q = q.filter(WorkflowInstanz.monat == monat)

    q = q.group_by(WorkflowInstanz.mandant_id, Mandant.name, WorkflowInstanz.monat, WorkflowInstanz.jahr)

    results = []
    for row in q.all():
        # Sonderaufgaben for this mandant/month
        so_punkte = db.query(func.coalesce(func.sum(Sonderaufgabe.punkte), 0)).filter(
            Sonderaufgabe.verantwortlicher_id == user_id,
            Sonderaufgabe.mandant_id == row.mandant_id,
            Sonderaufgabe.monat == row.monat,
            Sonderaufgabe.jahr == row.jahr,
            Sonderaufgabe.status == SonderaufgabeStatus.ABGESCHLOSSEN,
        ).scalar() or 0.0

        results.append(MandantPunkteDetail(
            mandant_id=row.mandant_id,
            mandant_name=row.mandant_name,
            monat=row.monat,
            jahr=row.jahr,
            punkte=row.punkte,
            sonderaufgaben_punkte=so_punkte,
        ))

    return results


# ─── Points Calculation for a Mandant ─────────────────────────

@router.get("/punkte/mandant/{mandant_id}")
def berechne_mandant_punkte(
    mandant_id: int,
    monat: int = Query(..., ge=1, le=12),
    jahr: int = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Calculate total points for a mandant-month based on the active PunkteKonfiguration."""
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    config = db.query(PunkteKonfiguration).filter(PunkteKonfiguration.ist_aktiv == True).first()
    if not config:
        return {"mandant_id": mandant_id, "punkte": 0, "details": "Keine Punktekonfiguration aktiv"}

    # Parse config
    kategorie_basis = json.loads(config.kategorie_basis)
    mitarbeiter_stufen = json.loads(config.mitarbeiter_stufen)
    branchen_faktoren = json.loads(config.branchen_faktoren) if config.branchen_faktoren else {}
    zusatzmodul_punkte = json.loads(config.zusatzmodul_punkte) if config.zusatzmodul_punkte else {}

    # 1. Basis points from category
    basis = kategorie_basis.get(mandant.kategorie.value if mandant.kategorie else "B", 5)

    # 2. Mitarbeiter factor
    ma_faktor = 1.0
    for stufe in mitarbeiter_stufen:
        if mandant.mitarbeiteranzahl <= stufe.get("bis", 99999):
            ma_faktor = stufe.get("faktor", 1.0)
            break

    # 3. Branchen factor
    branchen_faktor = 1.0
    for b in mandant.branchen_liste:
        f = branchen_faktoren.get(b.name, 1.0)
        if f > branchen_faktor:
            branchen_faktor = f

    # 4. Sonderaufgaben points for this month
    sonder_punkte = db.query(func.coalesce(func.sum(Sonderaufgabe.punkte), 0)).filter(
        Sonderaufgabe.mandant_id == mandant_id,
        Sonderaufgabe.monat == monat,
        Sonderaufgabe.jahr == jahr,
    ).scalar() or 0.0

    total = (basis * ma_faktor * branchen_faktor) + sonder_punkte

    return {
        "mandant_id": mandant_id,
        "monat": monat,
        "jahr": jahr,
        "punkte_gesamt": round(total, 2),
        "details": {
            "basis": basis,
            "mitarbeiter_faktor": ma_faktor,
            "branchen_faktor": branchen_faktor,
            "sonderaufgaben_punkte": sonder_punkte,
        },
    }


# ─── CSV Export ───────────────────────────────────────────────

@router.get("/punkte/export/csv")
def export_punkte_csv(
    jahr: int = Query(...),
    monat: Optional[int] = Query(None),
    quartal: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Export points report as CSV."""
    # Reuse the punkte_pro_mitarbeiter logic
    report = punkte_pro_mitarbeiter(monat=monat, jahr=jahr, quartal=quartal, db=db, _=_)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Mitarbeiter", "E-Mail", "Rolle", "Punkte Gesamt", "Punkte Workflows", "Punkte Sonderaufgaben", "Mandanten"])

    for row in report:
        writer.writerow([
            row.full_name, row.email, row.role.value,
            row.punkte_gesamt, row.punkte_workflows,
            row.punkte_sonderaufgaben, row.mandanten_count,
        ])

    output.seek(0)
    period = f"{monat}_{jahr}" if monat else f"Q{quartal}_{jahr}" if quartal else str(jahr)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=punkte_report_{period}.csv"},
    )


# ─── PunkteKonfiguration CRUD ────────────────────────────────

@router.get("/punkte/konfiguration")
def get_punkte_konfiguration(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    configs = db.query(PunkteKonfiguration).order_by(PunkteKonfiguration.id).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "kategorie_basis": json.loads(c.kategorie_basis),
            "mitarbeiter_stufen": json.loads(c.mitarbeiter_stufen),
            "branchen_faktoren": json.loads(c.branchen_faktoren) if c.branchen_faktoren else {},
            "zusatzmodul_punkte": json.loads(c.zusatzmodul_punkte) if c.zusatzmodul_punkte else {},
            "ist_aktiv": c.ist_aktiv,
        }
        for c in configs
    ]


def _quartal_monate(quartal: int) -> list:
    return {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}[quartal]
