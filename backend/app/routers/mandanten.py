from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import audit_service
from app.auth import get_current_user, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import (
    Mandant, MandantKategorie, User, MandantAenderung, Fristenprofil,
    Fristenregel, Sonderaufgabe, MandantKontakt, MandantNotiz,
    WorkflowInstanz, Ticket, TicketStatus, FristenVorlage,
)
from app.schemas import (
    MandantCreate, MandantOut, MandantUpdate, MandantAenderungOut,
    FristenprofilCreate, FristenprofilOut, FristenprofilUpdate,
    SonderaufgabeCreate, SonderaufgabeOut, SonderaufgabeUpdate,
    MandantKontaktCreate, MandantKontaktOut, MandantKontaktUpdate,
    MandantNotizCreate, MandantNotizOut,
)

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


# ─────────────────────────────────────────
# Fristenprofile
# ─────────────────────────────────────────

@router.get("/{mandant_id}/fristenprofil", response_model=FristenprofilOut)
def get_fristenprofil(
    mandant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    if not mandant.fristenprofil:
        raise HTTPException(status_code=404, detail="Kein Fristenprofil vorhanden")

    return mandant.fristenprofil


@router.post("/{mandant_id}/fristenprofil", response_model=FristenprofilOut, status_code=status.HTTP_201_CREATED)
def create_fristenprofil(
    mandant_id: int,
    data: FristenprofilCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    if mandant.fristenprofil:
        raise HTTPException(status_code=400, detail="Fristenprofil bereits vorhanden")

    profil = Fristenprofil(mandant_id=mandant_id, **data.model_dump(exclude={'regeln'}))
    db.add(profil)
    db.flush()

    for regel_data in data.regeln:
        regel = Fristenregel(profil_id=profil.id, **regel_data.model_dump())
        db.add(regel)

    audit_service.log(
        db,
        objekt_typ="fristenprofil",
        objekt_id=profil.id,
        mandant_id=mandant_id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert=data.model_dump(),
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Fristenprofil für Mandant '{mandant.name}' erstellt",
    )
    db.commit()
    db.refresh(profil)
    return profil


@router.patch("/{mandant_id}/fristenprofil", response_model=FristenprofilOut)
def update_fristenprofil(
    mandant_id: int,
    data: FristenprofilUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant or not mandant.fristenprofil:
        raise HTTPException(status_code=404, detail="Fristenprofil nicht gefunden")

    profil = mandant.fristenprofil
    update_data = data.model_dump(exclude_unset=True)
    old_vals = {k: getattr(profil, k) for k in update_data}

    for k, v in update_data.items():
        if k == 'regeln':
            # Handle regeln separately
            continue
        setattr(profil, k, v)

    audit_service.log(
        db,
        objekt_typ="fristenprofil",
        objekt_id=profil.id,
        mandant_id=mandant_id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old_vals,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Fristenprofil für Mandant '{mandant.name}' aktualisiert",
    )
    db.commit()
    db.refresh(profil)
    return profil


# ─────────────────────────────────────────
# Sonderaufgaben
# ─────────────────────────────────────────

@router.get("/{mandant_id}/sonderaufgaben", response_model=List[SonderaufgabeOut])
def list_sonderaufgaben(
    mandant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return db.query(Sonderaufgabe).filter(Sonderaufgabe.mandant_id == mandant_id).order_by(Sonderaufgabe.faellig_datum).all()


@router.post("/{mandant_id}/sonderaufgaben", response_model=SonderaufgabeOut, status_code=status.HTTP_201_CREATED)
def create_sonderaufgabe(
    mandant_id: int,
    data: SonderaufgabeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    aufgabe = Sonderaufgabe(mandant_id=mandant_id, erstellt_von_id=current_user.id, **data.model_dump())
    db.add(aufgabe)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="sonderaufgabe",
        objekt_id=aufgabe.id,
        mandant_id=mandant_id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert=data.model_dump(),
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Sonderaufgabe '{aufgabe.titel}' erstellt",
    )
    db.commit()
    db.refresh(aufgabe)
    return aufgabe


@router.patch("/{mandant_id}/sonderaufgaben/{aufgabe_id}", response_model=SonderaufgabeOut)
def update_sonderaufgabe(
    mandant_id: int,
    aufgabe_id: int,
    data: SonderaufgabeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    aufgabe = db.query(Sonderaufgabe).filter(
        Sonderaufgabe.id == aufgabe_id,
        Sonderaufgabe.mandant_id == mandant_id
    ).first()
    if not aufgabe:
        raise HTTPException(status_code=404, detail="Sonderaufgabe nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old_vals = {k: getattr(aufgabe, k) for k in update_data}

    for k, v in update_data.items():
        setattr(aufgabe, k, v)

    audit_service.log(
        db,
        objekt_typ="sonderaufgabe",
        objekt_id=aufgabe.id,
        mandant_id=mandant_id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old_vals,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Sonderaufgabe '{aufgabe.titel}' aktualisiert",
    )
    db.commit()
    db.refresh(aufgabe)
    return aufgabe


# ─────────────────────────────────────────
# Mandant Kontakte
# ─────────────────────────────────────────

@router.get("/{mandant_id}/kontakte", response_model=List[MandantKontaktOut])
def list_mandant_kontakte(
    mandant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return db.query(MandantKontakt).filter(MandantKontakt.mandant_id == mandant_id).order_by(MandantKontakt.name).all()


@router.post("/{mandant_id}/kontakte", response_model=MandantKontaktOut, status_code=status.HTTP_201_CREATED)
def create_mandant_kontakt(
    mandant_id: int,
    data: MandantKontaktCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    kontakt = MandantKontakt(mandant_id=mandant_id, **data.model_dump())
    db.add(kontakt)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="mandant_kontakt",
        objekt_id=kontakt.id,
        mandant_id=mandant_id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert=data.model_dump(),
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Kontakt '{kontakt.name}' für Mandant '{mandant.name}' erstellt",
    )
    db.commit()
    db.refresh(kontakt)
    return kontakt


@router.patch("/{mandant_id}/kontakte/{kontakt_id}", response_model=MandantKontaktOut)
def update_mandant_kontakt(
    mandant_id: int,
    kontakt_id: int,
    data: MandantKontaktUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    kontakt = db.query(MandantKontakt).filter(
        MandantKontakt.id == kontakt_id,
        MandantKontakt.mandant_id == mandant_id
    ).first()
    if not kontakt:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    old_vals = {k: getattr(kontakt, k) for k in update_data}

    for k, v in update_data.items():
        setattr(kontakt, k, v)

    audit_service.log(
        db,
        objekt_typ="mandant_kontakt",
        objekt_id=kontakt.id,
        mandant_id=mandant_id,
        aktionstyp="aktualisiert",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        alter_wert=old_vals,
        neuer_wert=update_data,
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Kontakt '{kontakt.name}' aktualisiert",
    )
    db.commit()
    db.refresh(kontakt)
    return kontakt


# ─────────────────────────────────────────
# Mandant Notizen
# ─────────────────────────────────────────

@router.get("/{mandant_id}/notizen", response_model=List[MandantNotizOut])
def list_mandant_notizen(
    mandant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return db.query(MandantNotiz).filter(MandantNotiz.mandant_id == mandant_id).order_by(MandantNotiz.version).all()


@router.post("/{mandant_id}/notizen", response_model=MandantNotizOut, status_code=status.HTTP_201_CREATED)
def create_mandant_notiz(
    mandant_id: int,
    data: MandantNotizCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    # Get next version
    max_version = db.query(MandantNotiz).filter(MandantNotiz.mandant_id == mandant_id).order_by(MandantNotiz.version.desc()).first()
    version = (max_version.version + 1) if max_version else 1

    notiz = MandantNotiz(mandant_id=mandant_id, version=version, erstellt_von_id=current_user.id, **data.model_dump())
    db.add(notiz)
    db.flush()

    audit_service.log(
        db,
        objekt_typ="mandant_notiz",
        objekt_id=notiz.id,
        mandant_id=mandant_id,
        aktionstyp="erstellt",
        benutzer_id=current_user.id,
        benutzerrolle=current_user.role.value,
        neuer_wert=data.model_dump(),
        ip_adresse=request.client.host if request.client else None,
        beschreibung=f"Notiz Version {version} für Mandant '{mandant.name}' erstellt",
    )
    db.commit()
    db.refresh(notiz)
    return notiz


# ─────────────────────────────────────────
# Geplante Änderungen Aktivierung
# ─────────────────────────────────────────

@router.post("/activate-planned-changes")
def activate_planned_changes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teamleitung),
):
    from datetime import datetime
    import json

    # Find all planned changes that are due
    due_changes = db.query(MandantAenderung).filter(
        MandantAenderung.status == "geplant",
        MandantAenderung.aenderung_zum <= datetime.utcnow()
    ).all()

    activated = []
    for change in due_changes:
        mandant = db.query(Mandant).filter(Mandant.id == change.mandant_id).first()
        if not mandant:
            continue

        old_vals = {}
        aenderungen = json.loads(change.aenderungen)
        for k, v in aenderungen.items():
            old_vals[k] = getattr(mandant, k)
            setattr(mandant, k, v)

        change.status = "aktiviert"
        change.aktiviert_am = datetime.utcnow()

        audit_service.log(
            db,
            objekt_typ="mandant",
            objekt_id=mandant.id,
            mandant_id=mandant.id,
            aktionstyp="geplante_aenderung_aktiviert",
            benutzer_id=current_user.id,
            benutzerrolle=current_user.role.value,
            alter_wert=old_vals,
            neuer_wert=aenderungen,
            ip_adresse=request.client.host if request.client else None,
            beschreibung=f"Geplante Änderung für Mandant '{mandant.name}' aktiviert",
        )
        activated.append(mandant.id)

    db.commit()
    return {"activated_mandanten": activated}


# ─────────────────────────────────────────
# One-Screen: Mandant-Month Combined View
# ─────────────────────────────────────────

@router.get("/{mandant_id}/monat/{monat}/{jahr}")
def mandant_monat_one_screen(
    mandant_id: int,
    monat: int,
    jahr: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Combined one-screen view for a mandant-month: workflow, tickets, sonderaufgaben, fristen, blockers."""
    import json as _json
    from app.bankarbeitstage import berechne_frist, berechne_frist_relativ
    from datetime import date

    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    # 1. Workflow
    workflow = db.query(WorkflowInstanz).filter(
        WorkflowInstanz.mandant_id == mandant_id,
        WorkflowInstanz.monat == monat,
        WorkflowInstanz.jahr == jahr,
    ).first()

    # 2. Tickets
    open_statuses = [
        TicketStatus.NEU, TicketStatus.OFFEN, TicketStatus.IN_BEARBEITUNG,
        TicketStatus.WARTET_AUF_MANDANT, TicketStatus.WARTET_INTERN,
        TicketStatus.INTERN_IN_KLAERUNG, TicketStatus.IN_PRUEFUNG,
    ]
    tickets = db.query(Ticket).filter(
        Ticket.mandant_id == mandant_id,
        Ticket.monat == monat,
        Ticket.jahr == jahr,
    ).order_by(Ticket.prioritaet.desc(), Ticket.created_at.desc()).all()

    # 3. Sonderaufgaben
    sonderaufgaben = db.query(Sonderaufgabe).filter(
        Sonderaufgabe.mandant_id == mandant_id,
        Sonderaufgabe.monat == monat,
        Sonderaufgabe.jahr == jahr,
    ).order_by(Sonderaufgabe.faellig_datum).all()

    # 4. Fristen (from Fristenprofil)
    fristen = []
    if mandant.fristenprofil:
        for regel in mandant.fristenprofil.regeln:
            if not regel.ist_aktiv:
                continue
            config = _json.loads(regel.regel_config)
            stichtag = berechne_frist(jahr, monat, regel.regeltyp.value, config, regel.bundesland)

            interne_vorfrist = None
            if stichtag and regel.interne_vorfrist_tage > 0:
                interne_vorfrist = berechne_frist_relativ(stichtag, -regel.interne_vorfrist_tage, regel.bundesland)

            heute = date.today()
            ampel = "gruen"
            if stichtag:
                if heute > stichtag:
                    ampel = "rot"
                elif interne_vorfrist and heute >= interne_vorfrist:
                    ampel = "gelb"

            vorlage = db.query(FristenVorlage).filter(FristenVorlage.code == regel.fristart).first()

            # Find affected workflow steps
            betroffene = []
            if workflow:
                for item in workflow.items:
                    if item.fristart_referenz == regel.fristart:
                        betroffene.append(item.titel)

            fristen.append({
                "fristart": regel.fristart,
                "name": vorlage.name if vorlage else regel.fristart,
                "externer_stichtag": stichtag.isoformat() if stichtag else None,
                "interne_vorfrist": interne_vorfrist.isoformat() if interne_vorfrist else None,
                "ampel": ampel,
                "betroffene_schritte": betroffene,
            })

    # 5. Blockers
    blocker = []
    open_critical_tickets = [
        t for t in tickets
        if t.status in open_statuses and t.prioritaet.value in ("kritisch", "dringend")
    ]
    for t in open_critical_tickets:
        blocker.append(f"Ticket #{t.id}: {t.titel} ({t.prioritaet.value})")

    # Check for missing documents in workflow
    if workflow:
        for item in workflow.items:
            if item.ist_blockiert:
                blocker.append(f"Schritt blockiert: {item.titel} – {item.blockiert_grund or ''}")

    return {
        "mandant_id": mandant_id,
        "mandant_name": mandant.name,
        "monat": monat,
        "jahr": jahr,
        "workflow": {
            "id": workflow.id,
            "status": workflow.status.value,
            "ampelstatus": workflow.ampelstatus.value,
            "items_total": len(workflow.items),
            "items_erledigt": sum(1 for i in workflow.items if i.status.value == "erledigt"),
            "sachbearbeiter": {"id": workflow.sachbearbeiter.id, "full_name": workflow.sachbearbeiter.full_name} if workflow.sachbearbeiter else None,
            "punkte": workflow.punkte,
        } if workflow else None,
        "tickets": [
            {
                "id": t.id,
                "titel": t.titel,
                "status": t.status.value,
                "prioritaet": t.prioritaet.value,
                "eskalationsstufe": t.eskalationsstufe.value if t.eskalationsstufe else None,
            }
            for t in tickets
        ],
        "sonderaufgaben": [
            {
                "id": s.id,
                "titel": s.titel,
                "kategorie": s.kategorie,
                "status": s.status.value,
                "punkte": s.punkte,
                "faellig_datum": s.faellig_datum.isoformat() if s.faellig_datum else None,
            }
            for s in sonderaufgaben
        ],
        "fristen": fristen,
        "blocker": blocker,
    }
