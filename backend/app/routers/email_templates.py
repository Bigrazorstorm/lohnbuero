"""Email template management and onboarding email dispatch."""
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import EmailLog, EmailLogStatus, EmailTemplate, Mandant, User
from app.schemas import (
    EmailLogOut,
    EmailTemplateCreate,
    EmailTemplateOut,
    EmailTemplateUpdate,
)

router = APIRouter(prefix="/api/email-templates", tags=["email-templates"])

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")

STANDARD_PLACEHOLDERS = {
    "Mandantenname": "Name des Mandanten",
    "Ansprechpartner": "Name des Ansprechpartners",
    "Fristdatum": "Abgabe-Frist (TT.MM.JJJJ)",
    "PortalLink": "Link zum Mandantenportal",
    "KanzleiName": "Name der Kanzlei",
    "SachbearbeiterName": "Zuständiger Sachbearbeiter",
}


# ── CRUD ────────────────────────────────────────────────

@router.get("/", response_model=List[EmailTemplateOut])
def list_templates(
    typ: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    q = db.query(EmailTemplate)
    if typ:
        q = q.filter(EmailTemplate.typ == typ)
    return q.order_by(EmailTemplate.reihenfolge, EmailTemplate.created_at).all()


@router.post("/", response_model=EmailTemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    data: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    tmpl = EmailTemplate(**data.model_dump())
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)

    audit_service.log(
        db,
        objekt_typ="email_template",
        objekt_id=tmpl.id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"name": tmpl.name, "typ": tmpl.typ},
        beschreibung=f"E-Mail-Template '{tmpl.name}' erstellt",
    )
    db.commit()
    return tmpl


@router.get("/{template_id}", response_model=EmailTemplateOut)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")
    return tmpl


@router.patch("/{template_id}", response_model=EmailTemplateOut)
def update_template(
    template_id: int,
    data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old = {k: getattr(tmpl, k) for k in update_data}
    for k, v in update_data.items():
        setattr(tmpl, k, v)
    tmpl.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tmpl)

    audit_service.log(
        db,
        objekt_typ="email_template",
        objekt_id=tmpl.id,
        aktionstyp="geaendert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old,
        neuer_wert=update_data,
        beschreibung=f"E-Mail-Template '{tmpl.name}' geändert",
    )
    db.commit()
    return tmpl


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")
    tmpl.ist_aktiv = False
    db.commit()


# ── Preview ─────────────────────────────────────────────

@router.post("/{template_id}/preview")
def preview_template(
    template_id: int,
    mandant_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")

    ctx = _build_context(db, mandant_id)
    return {
        "betreff": _render(tmpl.betreff, ctx),
        "html": _render(tmpl.html_inhalt, ctx),
        "text": _render(tmpl.text_inhalt or "", ctx),
    }


# ── Send (simulated – logs only, no SMTP) ───────────────

@router.post("/{template_id}/send", response_model=EmailLogOut, status_code=status.HTTP_201_CREATED)
def send_email(
    template_id: int,
    mandant_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")

    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    empfaenger = mandant.ansprechpartner_email or ""
    ctx = _build_context(db, mandant_id)

    email_log = EmailLog(
        template_id=tmpl.id,
        mandant_id=mandant_id,
        empfaenger=empfaenger,
        betreff=_render(tmpl.betreff, ctx),
        status=EmailLogStatus.GESENDET,
    )
    db.add(email_log)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="email",
        objekt_id=email_log.id,
        mandant_id=mandant_id,
        aktionstyp="versendet",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert={"template": tmpl.name, "empfaenger": empfaenger},
        beschreibung=f"E-Mail '{tmpl.name}' an {empfaenger} gesendet",
    )
    db.commit()
    db.refresh(email_log)
    return email_log


# ── Email log list ───────────────────────────────────────

@router.get("/logs/", response_model=List[EmailLogOut])
def list_email_logs(
    mandant_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    q = db.query(EmailLog)
    if mandant_id:
        q = q.filter(EmailLog.mandant_id == mandant_id)
    return q.order_by(EmailLog.gesendet_am.desc()).all()


# ── Internal helpers ─────────────────────────────────────

def _build_context(db: Session, mandant_id: Optional[int]) -> dict:
    ctx = {
        "Mandantenname": "Mustermann GmbH",
        "Ansprechpartner": "Herr Mustermann",
        "Fristdatum": "15.02.2026",
        "PortalLink": "https://portal.example.com",
        "KanzleiName": "Muster Kanzlei",
        "SachbearbeiterName": "Max Muster",
    }
    if mandant_id:
        mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
        if mandant:
            ctx["Mandantenname"] = mandant.name
            ctx["Ansprechpartner"] = mandant.ansprechpartner_name or mandant.name
            if mandant.sachbearbeiter:
                ctx["SachbearbeiterName"] = mandant.sachbearbeiter.full_name
    return ctx


def _render(template: str, ctx: dict) -> str:
    if not template:
        return ""
    for key, val in ctx.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return template


def send_onboarding_emails(db: Session, mandant: Mandant) -> None:
    """Trigger onboarding email sequence for a newly created mandant."""
    templates = (
        db.query(EmailTemplate)
        .filter(EmailTemplate.typ.like("onboarding%"), EmailTemplate.ist_aktiv == True)
        .order_by(EmailTemplate.reihenfolge)
        .all()
    )
    if not templates:
        return

    empfaenger = mandant.ansprechpartner_email or ""
    ctx = _build_context(db, mandant.id)

    for tmpl in templates:
        email_log = EmailLog(
            template_id=tmpl.id,
            mandant_id=mandant.id,
            empfaenger=empfaenger,
            betreff=_render(tmpl.betreff, ctx),
            status=EmailLogStatus.GESENDET,
        )
        db.add(email_log)

        audit_service.log(
            db,
            objekt_typ="email",
            mandant_id=mandant.id,
            aktionstyp="onboarding_versendet",
            neuer_wert={"template": tmpl.name, "empfaenger": empfaenger},
            beschreibung=f"Onboarding-E-Mail '{tmpl.name}' an {empfaenger or '(kein Empfänger)'} gesendet",
        )
    # Caller must commit.
