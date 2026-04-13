from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import BenutzerRolle
from app.models.benutzer import Benutzer
from app.schemas.benutzer import BenutzerRolleUpdate


def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Benutzer]:
    return db.query(Benutzer).offset(skip).limit(limit).all()


def get_by_id(db: Session, benutzer_id: int) -> Benutzer:
    benutzer = db.get(Benutzer, benutzer_id)
    if benutzer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden.")
    return benutzer


def update_rolle(db: Session, benutzer_id: int, payload: BenutzerRolleUpdate) -> Benutzer:
    benutzer = get_by_id(db, benutzer_id)
    benutzer.rolle = payload.rolle
    db.commit()
    db.refresh(benutzer)
    return benutzer


def delete(db: Session, benutzer_id: int, admin_id: int) -> None:
    benutzer = get_by_id(db, benutzer_id)
    if benutzer.id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Du kannst deinen eigenen Account nicht löschen.",
        )
    db.delete(benutzer)
    db.commit()
