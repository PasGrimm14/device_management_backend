from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.base import AktionType, GeraeteStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet
from app.schemas.geraet import GeraetCreate, GeraetResponse, GeraetUpdate

router = APIRouter()


def _write_audit(
    db: Session,
    nutzer_id: int,
    aktion: AktionType,
    geraet_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    db.add(AuditLog(nutzer_id=nutzer_id, geraet_id=geraet_id, aktion=aktion, details=details))


@router.get("/", response_model=list[GeraetResponse])
def list_geraete(
    status: Optional[GeraeteStatus] = Query(default=None),
    kategorie: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> list[Geraet]:
    """Gibt alle Geräte zurück. Filterbar nach Status und Kategorie."""
    q = db.query(Geraet)
    if status is not None:
        q = q.filter(Geraet.status == status)
    if kategorie is not None:
        q = q.filter(Geraet.kategorie == kategorie)
    return q.offset(skip).limit(limit).all()


@router.get("/{geraet_id}", response_model=GeraetResponse)
def get_geraet(
    geraet_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> Geraet:
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    return geraet


@router.post("/", response_model=GeraetResponse, status_code=status.HTTP_201_CREATED)
def create_geraet(
    payload: GeraetCreate,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
) -> Geraet:
    """Legt ein neues Gerät an. Nur für Administratoren."""
    if db.query(Geraet).filter(Geraet.inventar_nummer == payload.inventar_nummer).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inventarnummer '{payload.inventar_nummer}' ist bereits vergeben.",
        )
    geraet = Geraet(**payload.model_dump())
    db.add(geraet)
    db.flush()
    _write_audit(db, admin.id, AktionType.ANGELEGT, geraet.id, f"Gerät '{geraet.name}' angelegt.")
    db.commit()
    db.refresh(geraet)
    return geraet


@router.patch("/{geraet_id}", response_model=GeraetResponse)
def update_geraet(
    geraet_id: int,
    payload: GeraetUpdate,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
) -> Geraet:
    """Aktualisiert einzelne Felder eines Geräts (PATCH). Nur für Administratoren."""
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")

    changes = payload.model_dump(exclude_unset=True)
    old_status = geraet.status

    for field, value in changes.items():
        setattr(geraet, field, value)

    aktion = AktionType.STATUS_AENDERUNG if "status" in changes else AktionType.BEARBEITET
    details = f"Status: {old_status} → {geraet.status}" if "status" in changes else str(changes)
    _write_audit(db, admin.id, aktion, geraet.id, details)
    db.commit()
    db.refresh(geraet)
    return geraet


@router.delete("/{geraet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_geraet(
    geraet_id: int,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
) -> None:
    """Löscht ein Gerät. Nur für Administratoren."""
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    db.delete(geraet)
    db.commit()
