from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import ausleihen as crud
from app.models.benutzer import Benutzer
from app.schemas.ausleihe import AusleiheCreate, AusleiheResponse

router = APIRouter()


@router.get("/", response_model=list[AusleiheResponse])
def list_ausleihen(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.get_all(db, current_user, skip=skip, limit=limit)


@router.get("/{ausleihe_id}", response_model=AusleiheResponse)
def get_ausleihe(
    ausleihe_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.get_by_id(db, ausleihe_id, current_user)


@router.post("/", response_model=AusleiheResponse, status_code=201)
def create_ausleihe(
    payload: AusleiheCreate,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.create(db, payload, current_user)


@router.post("/{ausleihe_id}/verlaengern", response_model=AusleiheResponse)
def verlaengern(
    ausleihe_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.verlaengern(db, ausleihe_id, current_user)


@router.post("/{ausleihe_id}/rueckgabe", response_model=AusleiheResponse)
def rueckgabe(
    ausleihe_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.rueckgabe(db, ausleihe_id, current_user)
