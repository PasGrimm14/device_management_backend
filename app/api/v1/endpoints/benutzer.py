from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.crud import benutzer as crud
from app.models.benutzer import Benutzer
from app.schemas.benutzer import BenutzerResponse, BenutzerRolleUpdate

router = APIRouter()


@router.get("/me", response_model=BenutzerResponse)
def get_me(current_user: Benutzer = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[BenutzerResponse])
def list_benutzer(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    return crud.get_all(db, skip=skip, limit=limit)


@router.get("/{benutzer_id}", response_model=BenutzerResponse)
def get_benutzer(
    benutzer_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    return crud.get_by_id(db, benutzer_id)


@router.patch("/{benutzer_id}/rolle", response_model=BenutzerResponse)
def update_rolle(
    benutzer_id: int,
    payload: BenutzerRolleUpdate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    return crud.update_rolle(db, benutzer_id, payload)


@router.delete("/{benutzer_id}", status_code=204)
def delete_benutzer(
    benutzer_id: int,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
):
    crud.delete(db, benutzer_id, admin.id)
