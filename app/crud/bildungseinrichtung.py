from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.bildungseinrichtung import Bildungseinrichtung
from app.schemas.bildungseinrichtung import BildungseinrichtungCreate, BildungseinrichtungUpdate


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[Bildungseinrichtung]:
    """Gibt alle Bildungseinrichtungen paginiert zurück."""
    return db.query(Bildungseinrichtung).offset(skip).limit(limit).all()


def get_by_id(db: Session, bildungseinrichtung_id: int) -> Bildungseinrichtung:
    """Gibt eine Bildungseinrichtung anhand ihrer ID zurück oder wirft 404."""
    einrichtung = db.get(Bildungseinrichtung, bildungseinrichtung_id)
    if einrichtung is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bildungseinrichtung nicht gefunden.",
        )
    return einrichtung


def create(db: Session, payload: BildungseinrichtungCreate) -> Bildungseinrichtung:
    """Legt eine neue Bildungseinrichtung an."""
    einrichtung = Bildungseinrichtung(**payload.model_dump())
    db.add(einrichtung)
    db.commit()
    db.refresh(einrichtung)
    return einrichtung


def update(
    db: Session,
    bildungseinrichtung_id: int,
    payload: BildungseinrichtungUpdate,
) -> Bildungseinrichtung:
    """Aktualisiert eine bestehende Bildungseinrichtung (partial update)."""
    einrichtung = get_by_id(db, bildungseinrichtung_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(einrichtung, field, value)
    db.commit()
    db.refresh(einrichtung)
    return einrichtung


def delete(db: Session, bildungseinrichtung_id: int) -> None:
    """Löscht eine Bildungseinrichtung. Wirft 404, wenn sie nicht existiert."""
    einrichtung = get_by_id(db, bildungseinrichtung_id)
    db.delete(einrichtung)
    db.commit()
