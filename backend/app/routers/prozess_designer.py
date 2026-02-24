"""
Prozessdesigner API – Verwaltet den visuellen Prozessdesigner.

Ermöglicht:
- Abruf des vollständigen Prozessgraphen (Knoten + Kanten) für eine Workflow-Vorlage
- Aktualisierung der Canvas-Position einzelner Prozessschritte
- Verwaltung von Checklisten-Einträgen pro Prozessschritt
- Verwaltung von Abhängigkeiten (Kanten) zwischen Prozessschritten
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_admin, require_admin_or_teamleitung, require_staff
from app.database import get_db
from app.models import (
    ProzessSchrittChecklistItem, User, WorkflowVorlage, WorkflowVorlageItem,
    WorkflowVorlageItemDependency, WorkflowItemDependencyTyp,
)
from app.schemas import (
    ProzessDesignerGraph,
    ProzessDesignerPositionUpdate,
    ProzessSchrittChecklistItemCreate,
    ProzessSchrittChecklistItemOut,
    ProzessSchrittChecklistItemUpdate,
    WorkflowVorlageItemDependencyOut,
    WorkflowPhaseOut,
)

router = APIRouter(prefix="/api/admin/prozess-designer", tags=["prozess-designer"])


# ═══════════════════════════════════════════
# Graph-Abfrage
# ═══════════════════════════════════════════

@router.get("/vorlagen", summary="Listet alle Workflow-Vorlagen für den Prozessdesigner")
def list_vorlagen(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Gibt eine Liste aller verfügbaren Workflow-Vorlagen zurück."""
    vorlagen = db.query(WorkflowVorlage).order_by(WorkflowVorlage.name).all()
    return [{"id": v.id, "name": v.name, "beschreibung": v.beschreibung, "ist_standard": v.ist_standard} for v in vorlagen]


@router.get("/{vorlage_id}", response_model=ProzessDesignerGraph, summary="Gibt den Prozessgraph einer Vorlage zurück")
def get_prozess_graph(
    vorlage_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """
    Gibt den vollständigen Prozessgraph einer Workflow-Vorlage zurück:
    - nodes: Alle Prozessschritte mit Positionen und Checklisten
    - edges: Alle Abhängigkeiten zwischen Schritten
    - phasen: Alle Phasen der Vorlage
    """
    vorlage = db.query(WorkflowVorlage).filter(WorkflowVorlage.id == vorlage_id).first()
    if not vorlage:
        raise HTTPException(status_code=404, detail="Workflow-Vorlage nicht gefunden")

    # Auto-layout: wenn pos_x/pos_y noch 0, berechne initiale Positionen
    items = sorted(vorlage.items, key=lambda x: x.position)
    has_positions = any(item.pos_x != 0.0 or item.pos_y != 0.0 for item in items)

    if not has_positions and items:
        _auto_layout(db, items, vorlage.item_dependencies)

    return ProzessDesignerGraph(
        vorlage_id=vorlage.id,
        vorlage_name=vorlage.name,
        nodes=items,
        edges=vorlage.item_dependencies,
        phasen=sorted(vorlage.phasen, key=lambda p: p.position) if vorlage.phasen else [],
    )


def _auto_layout(db: Session, items: list, dependencies: list):
    """
    Berechnet initiale Canvas-Positionen für Prozessschritte ohne vorhandene Positionen.
    Verwendet einen einfachen Layered-Layout-Algorithmus basierend auf Abhängigkeiten.
    """
    CARD_WIDTH = 220
    CARD_HEIGHT = 120
    H_SPACING = 80
    V_SPACING = 60

    # Build adjacency: which items depend on which
    dep_map: dict[int, set[int]] = {item.id: set() for item in items}
    for dep in dependencies:
        dep_map.setdefault(dep.target_item_id, set()).add(dep.source_item_id)

    # Assign layers (topological sort)
    item_by_id = {item.id: item for item in items}
    layers: dict[int, int] = {}

    def get_layer(item_id: int, visited: set) -> int:
        if item_id in layers:
            return layers[item_id]
        if item_id in visited:
            return 0  # cycle fallback
        visited.add(item_id)
        preds = dep_map.get(item_id, set())
        layer = max((get_layer(p, visited) for p in preds), default=-1) + 1
        layers[item_id] = layer
        return layer

    for item in items:
        get_layer(item.id, set())

    # Group items by layer
    layer_groups: dict[int, list] = {}
    for item in items:
        layer = layers.get(item.id, 0)
        layer_groups.setdefault(layer, []).append(item)

    # Assign positions
    x = 60
    for layer_idx in sorted(layer_groups.keys()):
        layer_items = layer_groups[layer_idx]
        for j, item in enumerate(layer_items):
            item.pos_x = float(x)
            item.pos_y = float(60 + j * (CARD_HEIGHT + V_SPACING))
        x += CARD_WIDTH + H_SPACING

    db.commit()


# ═══════════════════════════════════════════
# Knotenposition aktualisieren
# ═══════════════════════════════════════════

@router.patch(
    "/items/{item_id}/position",
    summary="Aktualisiert die Canvas-Position eines Prozessschritts",
)
def update_item_position(
    item_id: int,
    data: ProzessDesignerPositionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Speichert die neue Canvas-Position eines Prozessschritts nach dem Verschieben."""
    item = db.query(WorkflowVorlageItem).filter(WorkflowVorlageItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Prozessschritt nicht gefunden")

    item.pos_x = data.pos_x
    item.pos_y = data.pos_y
    db.commit()
    return {"ok": True, "pos_x": item.pos_x, "pos_y": item.pos_y}


# ═══════════════════════════════════════════
# Abhängigkeiten (Kanten) verwalten
# ═══════════════════════════════════════════

@router.post(
    "/{vorlage_id}/edges",
    response_model=WorkflowVorlageItemDependencyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Erstellt eine neue Abhängigkeit (Kante) zwischen zwei Prozessschritten",
)
def create_edge(
    vorlage_id: int,
    source_item_id: int,
    target_item_id: int,
    typ: str = "blockiert_von",
    beschreibung: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """
    Erstellt eine neue Abhängigkeit zwischen zwei Prozessschritten.
    - source_item_id: Der Schritt, der zuerst fertig sein muss
    - target_item_id: Der Schritt, der blockiert ist bis source fertig ist
    """
    vorlage = db.query(WorkflowVorlage).filter(WorkflowVorlage.id == vorlage_id).first()
    if not vorlage:
        raise HTTPException(status_code=404, detail="Workflow-Vorlage nicht gefunden")

    # Validate items belong to this vorlage
    source = db.query(WorkflowVorlageItem).filter(
        WorkflowVorlageItem.id == source_item_id,
        WorkflowVorlageItem.vorlage_id == vorlage_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Quell-Schritt nicht gefunden")

    target = db.query(WorkflowVorlageItem).filter(
        WorkflowVorlageItem.id == target_item_id,
        WorkflowVorlageItem.vorlage_id == vorlage_id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Ziel-Schritt nicht gefunden")

    # Avoid duplicate edges
    existing = db.query(WorkflowVorlageItemDependency).filter(
        WorkflowVorlageItemDependency.vorlage_id == vorlage_id,
        WorkflowVorlageItemDependency.source_item_id == source_item_id,
        WorkflowVorlageItemDependency.target_item_id == target_item_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Diese Abhängigkeit existiert bereits")

    try:
        dep_typ = WorkflowItemDependencyTyp(typ)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unbekannter Abhängigkeitstyp: {typ}")

    dep = WorkflowVorlageItemDependency(
        vorlage_id=vorlage_id,
        source_item_id=source_item_id,
        target_item_id=target_item_id,
        typ=dep_typ,
        beschreibung=beschreibung,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete(
    "/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Löscht eine Abhängigkeit (Kante) zwischen zwei Prozessschritten",
)
def delete_edge(
    edge_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Entfernt eine Abhängigkeit (Verbindungspfeil) zwischen zwei Prozessschritten."""
    dep = db.query(WorkflowVorlageItemDependency).filter(
        WorkflowVorlageItemDependency.id == edge_id
    ).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Abhängigkeit nicht gefunden")
    db.delete(dep)
    db.commit()


# ═══════════════════════════════════════════
# Checklisten pro Prozessschritt
# ═══════════════════════════════════════════

@router.get(
    "/items/{item_id}/checklisten",
    response_model=List[ProzessSchrittChecklistItemOut],
    summary="Gibt alle Checklisten-Einträge eines Prozessschritts zurück",
)
def list_checklisten(
    item_id: int,
    nur_aktive: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Listet alle Checklisten-Einträge für einen Prozessschritt auf."""
    item = db.query(WorkflowVorlageItem).filter(WorkflowVorlageItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Prozessschritt nicht gefunden")

    q = db.query(ProzessSchrittChecklistItem).filter(
        ProzessSchrittChecklistItem.vorlage_item_id == item_id
    )
    if nur_aktive:
        q = q.filter(ProzessSchrittChecklistItem.ist_aktiv == True)
    return q.order_by(ProzessSchrittChecklistItem.position).all()


@router.post(
    "/items/{item_id}/checklisten",
    response_model=ProzessSchrittChecklistItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Erstellt einen neuen Checklisten-Eintrag für einen Prozessschritt",
)
def create_checklist_item(
    item_id: int,
    data: ProzessSchrittChecklistItemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Fügt einen neuen Checklisten-Eintrag zu einem Prozessschritt hinzu."""
    item = db.query(WorkflowVorlageItem).filter(WorkflowVorlageItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Prozessschritt nicht gefunden")

    checklist_item = ProzessSchrittChecklistItem(
        vorlage_item_id=item_id,
        **data.model_dump(),
    )
    db.add(checklist_item)
    db.commit()
    db.refresh(checklist_item)
    return checklist_item


@router.patch(
    "/checklisten/{checklist_id}",
    response_model=ProzessSchrittChecklistItemOut,
    summary="Aktualisiert einen Checklisten-Eintrag",
)
def update_checklist_item(
    checklist_id: int,
    data: ProzessSchrittChecklistItemUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Aktualisiert einen bestehenden Checklisten-Eintrag."""
    checklist_item = db.query(ProzessSchrittChecklistItem).filter(
        ProzessSchrittChecklistItem.id == checklist_id
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklisten-Eintrag nicht gefunden")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(checklist_item, key, value)

    db.commit()
    db.refresh(checklist_item)
    return checklist_item


@router.delete(
    "/checklisten/{checklist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Löscht einen Checklisten-Eintrag",
)
def delete_checklist_item(
    checklist_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teamleitung),
):
    """Entfernt einen Checklisten-Eintrag aus einem Prozessschritt."""
    checklist_item = db.query(ProzessSchrittChecklistItem).filter(
        ProzessSchrittChecklistItem.id == checklist_id
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklisten-Eintrag nicht gefunden")
    db.delete(checklist_item)
    db.commit()
