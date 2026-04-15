from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.base import AktionType, GeraeteStatus
from app.models.geraet import Geraet
from app.schemas.geraet import GeraetCreate, GeraetUpdate


def get_all(
    db: Session,
    *,
    filter_status: Optional[GeraeteStatus] = None,
    filter_kategorie: Optional[str] = None,
    filter_search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Geraet]:
    q = db.query(Geraet)
    if filter_status is not None:
        q = q.filter(Geraet.status == filter_status)
    if filter_kategorie is not None:
        q = q.filter(Geraet.kategorie == filter_kategorie)
    if filter_search is not None:
        term = f"%{filter_search}%"
        q = q.filter(
            Geraet.name.ilike(term)
            | Geraet.hersteller.ilike(term)
            | Geraet.modell.ilike(term)
            | Geraet.inventar_nummer.ilike(term)
        )
    return q.offset(skip).limit(limit).all()


def get_by_id(db: Session, geraet_id: int) -> Geraet:
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    return geraet


def create(db: Session, payload: GeraetCreate, nutzer_id: int) -> Geraet:
    if db.query(Geraet).filter(Geraet.inventar_nummer == payload.inventar_nummer).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inventarnummer '{payload.inventar_nummer}' ist bereits vergeben.",
        )
    geraet = Geraet(**payload.model_dump())
    db.add(geraet)
    db.flush()
    db.add(AuditLog(
        nutzer_id=nutzer_id,
        geraet_id=geraet.id,
        aktion=AktionType.ANGELEGT,
        details=f"Gerät '{geraet.name}' angelegt.",
    ))
    db.commit()
    db.refresh(geraet)
    return geraet


def update(db: Session, geraet_id: int, payload: GeraetUpdate, nutzer_id: int) -> Geraet:
    geraet = get_by_id(db, geraet_id)
    changes = payload.model_dump(exclude_unset=True)
    old_status = geraet.status

    for field, value in changes.items():
        setattr(geraet, field, value)

    aktion = AktionType.STATUS_AENDERUNG if "status" in changes else AktionType.BEARBEITET
    details = f"Status: {old_status} → {geraet.status}" if "status" in changes else str(changes)
    db.add(AuditLog(nutzer_id=nutzer_id, geraet_id=geraet.id, aktion=aktion, details=details))
    db.commit()
    db.refresh(geraet)
    return geraet


def delete(db: Session, geraet_id: int) -> None:
    geraet = get_by_id(db, geraet_id)
    db.delete(geraet)
    db.commit()
