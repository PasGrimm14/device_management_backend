from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.models.benutzer import Benutzer
from app.schemas.benutzer import BenutzerResponse, BenutzerRolleUpdate

router = APIRouter()


@router.get("/me", response_model=BenutzerResponse)
def get_me(current_user: Benutzer = Depends(get_current_user)) -> Benutzer:
    """Gibt das Profil des eingeloggten Benutzers zurück."""
    return current_user


@router.get("/", response_model=list[BenutzerResponse])
def list_benutzer(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> list[Benutzer]:
    """Gibt alle Benutzer zurück. Nur für Administratoren."""
    return db.query(Benutzer).offset(skip).limit(limit).all()


@router.get("/{benutzer_id}", response_model=BenutzerResponse)
def get_benutzer(
    benutzer_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> Benutzer:
    """Gibt einen einzelnen Benutzer zurück. Nur für Administratoren."""
    benutzer = db.get(Benutzer, benutzer_id)
    if benutzer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden.")
    return benutzer


@router.patch("/{benutzer_id}/rolle", response_model=BenutzerResponse)
def update_rolle(
    benutzer_id: int,
    payload: BenutzerRolleUpdate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> Benutzer:
    """Ändert die Rolle eines Benutzers. Nur für Administratoren."""
    benutzer = db.get(Benutzer, benutzer_id)
    if benutzer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden.")
    benutzer.rolle = payload.rolle
    db.commit()
    db.refresh(benutzer)
    return benutzer


@router.delete("/{benutzer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_benutzer(
    benutzer_id: int,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
) -> None:
    """Löscht einen Benutzer. Nur für Administratoren."""
    benutzer = db.get(Benutzer, benutzer_id)
    if benutzer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden.")
    if benutzer.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Du kannst deinen eigenen Account nicht löschen.",
        )
    db.delete(benutzer)
    db.commit()
