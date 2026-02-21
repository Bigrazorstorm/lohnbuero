import os
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Dokument, Mandant, User, UserRole
from app.schemas import DokumentOut

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/dokumente", tags=["dokumente"])


@router.get("/", response_model=List[DokumentOut])
def list_dokumente(
    mandant_id: Optional[int] = Query(None),
    workflow_instanz_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Dokument)

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if mandant:
            q = q.filter(Dokument.mandant_id == mandant.id)
        else:
            return []
    else:
        if mandant_id:
            q = q.filter(Dokument.mandant_id == mandant_id)
        if workflow_instanz_id:
            q = q.filter(Dokument.workflow_instanz_id == workflow_instanz_id)

    return q.order_by(Dokument.created_at.desc()).all()


@router.post("/upload", response_model=DokumentOut, status_code=status.HTTP_201_CREATED)
async def upload_dokument(
    mandant_id: int = Form(...),
    workflow_instanz_id: Optional[int] = Form(None),
    workflow_item_id: Optional[int] = Form(None),
    kategorie: Optional[str] = Form(None),
    notiz: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mandant = db.query(Mandant).filter(Mandant.id == mandant_id).first()
    if not mandant:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    if current_user.role == UserRole.MANDANT and mandant.portal_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    # Save file
    dest_dir = os.path.join(UPLOAD_DIR, str(mandant_id))
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(file_path)
    ext = os.path.splitext(file.filename)[1].lower()

    doc = Dokument(
        mandant_id=mandant_id,
        workflow_instanz_id=workflow_instanz_id,
        workflow_item_id=workflow_item_id,
        hochgeladen_von_id=current_user.id,
        name=file.filename,
        dateityp=ext,
        dateigroesse=file_size,
        speicherort=file_path,
        kategorie=kategorie,
        notiz=notiz,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{dokument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dokument(
    dokument_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Dokument).filter(Dokument.id == dokument_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")

    if current_user.role == UserRole.MANDANT:
        mandant = db.query(Mandant).filter(Mandant.portal_user_id == current_user.id).first()
        if not mandant or mandant.id != doc.mandant_id:
            raise HTTPException(status_code=403, detail="Keine Berechtigung")

    # Remove file from disk
    if doc.speicherort and os.path.exists(doc.speicherort):
        os.remove(doc.speicherort)

    db.delete(doc)
    db.commit()
