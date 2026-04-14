from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.standort import Standort
from app.schemas.standort import StandortCreate, StandortUpdate


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[Standort]:
    """Gibt alle Standorte paginiert zurück."""
    return db.query(Standort).offset(skip).limit(limit).all()


def get_by_id(db: Session, standort_id: int) -> Standort:
    """Gibt einen Standort anhand seiner ID zurück oder wirft 404."""
    standort = db.get(Standort, standort_id)
    if standort is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Standort nicht gefunden.",
        )
    return standort


def create(db: Session, payload: StandortCreate) -> Standort:
    """Legt einen neuen Standort an."""
    standort = Standort(**payload.model_dump())
    db.add(standort)
    db.commit()
    db.refresh(standort)
    return standort


def update(db: Session, standort_id: int, payload: StandortUpdate) -> Standort:
    """Aktualisiert einen bestehenden Standort (partial update)."""
    standort = get_by_id(db, standort_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(standort, field, value)
    db.commit()
    db.refresh(standort)
    return standort


def delete(db: Session, standort_id: int) -> None:
    """Löscht einen Standort. Wirft 404, wenn er nicht existiert."""
    standort = get_by_id(db, standort_id)
    db.delete(standort)
    db.commit()
