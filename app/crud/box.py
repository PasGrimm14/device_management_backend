from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.box import Box
from app.schemas.box import BoxCreate, BoxUpdate


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[Box]:
    """Gibt alle Boxen paginiert zurück."""
    return db.query(Box).offset(skip).limit(limit).all()


def get_by_id(db: Session, box_id: int) -> Box:
    """Gibt eine Box anhand ihrer ID zurück oder wirft 404."""
    box = db.get(Box, box_id)
    if box is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Box nicht gefunden.",
        )
    return box


def create(db: Session, payload: BoxCreate) -> Box:
    """Legt eine neue Box an."""
    box = Box(**payload.model_dump())
    db.add(box)
    db.commit()
    db.refresh(box)
    return box


def update(db: Session, box_id: int, payload: BoxUpdate) -> Box:
    """Aktualisiert eine bestehende Box (partial update)."""
    box = get_by_id(db, box_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(box, field, value)
    db.commit()
    db.refresh(box)
    return box


def delete(db: Session, box_id: int) -> None:
    """Löscht eine Box. Wirft 404, wenn sie nicht existiert."""
    box = get_by_id(db, box_id)
    db.delete(box)
    db.commit()
