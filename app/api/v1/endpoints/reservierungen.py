from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import reservierungen as crud
from app.models.benutzer import Benutzer
from app.schemas.reservierung import ReservierungCreate, ReservierungResponse

router = APIRouter()


@router.get("/", response_model=list[ReservierungResponse])
def list_reservierungen(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.get_all(db, current_user, skip=skip, limit=limit)


@router.post("/", response_model=ReservierungResponse, status_code=201)
def create_reservierung(
    payload: ReservierungCreate,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.create(db, payload, current_user)


@router.delete("/{reservierung_id}", status_code=204)
def storniere_reservierung(
    reservierung_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    crud.stornieren(db, reservierung_id, current_user)
