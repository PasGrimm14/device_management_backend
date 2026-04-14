from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.crud import geraete as crud
from app.crud import geraet_bilder as crud_bilder
from app.models.base import GeraeteStatus
from app.models.benutzer import Benutzer
from app.schemas.geraet import GeraetCreate, GeraetResponse, GeraetUpdate
from app.schemas.geraet_bild import GeraetBildUrlResponse

router = APIRouter()


@router.get("/", response_model=list[GeraetResponse])
def list_geraete(
    status: Optional[GeraeteStatus] = Query(default=None),
    kategorie: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
):
    return crud.get_all(db, filter_status=status, filter_kategorie=kategorie, skip=skip, limit=limit)


@router.get("/{geraet_id}", response_model=GeraetResponse)
def get_geraet(
    geraet_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
):
    return crud.get_by_id(db, geraet_id)


@router.post("/", response_model=GeraetResponse, status_code=201)
def create_geraet(
    payload: GeraetCreate,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
):
    return crud.create(db, payload, admin.id)


@router.patch("/{geraet_id}", response_model=GeraetResponse)
def update_geraet(
    geraet_id: int,
    payload: GeraetUpdate,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
):
    return crud.update(db, geraet_id, payload, admin.id)


@router.delete("/{geraet_id}", status_code=204)
def delete_geraet(
    geraet_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    crud.delete(db, geraet_id)


@router.get("/{geraet_id}/bild", response_model=GeraetBildUrlResponse)
def get_geraet_bild(
    geraet_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
):
    """Gibt eine Presigned-URL (1 Stunde) für das Bild des Geräts zurück."""
    url = crud_bilder.get_presigned_url(db, geraet_id)
    return GeraetBildUrlResponse(presigned_url=url)
