from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.crud import bildungseinrichtung as crud_einrichtung
from app.crud import box as crud_box
from app.crud import standort as crud_standort
from app.models.benutzer import Benutzer
from app.schemas.bildungseinrichtung import (
    BildungseinrichtungCreate,
    BildungseinrichtungResponse,
    BildungseinrichtungUpdate,
)
from app.schemas.box import BoxCreate, BoxResponse, BoxUpdate
from app.schemas.standort import StandortCreate, StandortResponse, StandortUpdate

bildungseinrichtungen_router = APIRouter()
standorte_router = APIRouter()
boxen_router = APIRouter()


# ---------------------------------------------------------------------------
# Bildungseinrichtungen
# ---------------------------------------------------------------------------

@bildungseinrichtungen_router.get("/", response_model=list[BildungseinrichtungResponse])
def list_bildungseinrichtungen(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> list[BildungseinrichtungResponse]:
    """Gibt alle Bildungseinrichtungen paginiert zurück."""
    return crud_einrichtung.get_all(db, skip=skip, limit=limit)


@bildungseinrichtungen_router.get("/{einrichtung_id}", response_model=BildungseinrichtungResponse)
def get_bildungseinrichtung(
    einrichtung_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> BildungseinrichtungResponse:
    """Gibt eine einzelne Bildungseinrichtung anhand ihrer ID zurück."""
    return crud_einrichtung.get_by_id(db, einrichtung_id)


@bildungseinrichtungen_router.post("/", response_model=BildungseinrichtungResponse, status_code=201)
def create_bildungseinrichtung(
    payload: BildungseinrichtungCreate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> BildungseinrichtungResponse:
    """Legt eine neue Bildungseinrichtung an (nur Admins)."""
    return crud_einrichtung.create(db, payload)


@bildungseinrichtungen_router.put("/{einrichtung_id}", response_model=BildungseinrichtungResponse)
def update_bildungseinrichtung(
    einrichtung_id: int,
    payload: BildungseinrichtungUpdate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> BildungseinrichtungResponse:
    """Aktualisiert eine Bildungseinrichtung (nur Admins)."""
    return crud_einrichtung.update(db, einrichtung_id, payload)


@bildungseinrichtungen_router.delete("/{einrichtung_id}", status_code=204)
def delete_bildungseinrichtung(
    einrichtung_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> None:
    """Löscht eine Bildungseinrichtung (nur Admins)."""
    crud_einrichtung.delete(db, einrichtung_id)


# ---------------------------------------------------------------------------
# Standorte
# ---------------------------------------------------------------------------

@standorte_router.get("/", response_model=list[StandortResponse])
def list_standorte(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> list[StandortResponse]:
    """Gibt alle Standorte paginiert zurück."""
    return crud_standort.get_all(db, skip=skip, limit=limit)


@standorte_router.get("/{standort_id}", response_model=StandortResponse)
def get_standort(
    standort_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> StandortResponse:
    """Gibt einen einzelnen Standort anhand seiner ID zurück."""
    return crud_standort.get_by_id(db, standort_id)


@standorte_router.post("/", response_model=StandortResponse, status_code=201)
def create_standort(
    payload: StandortCreate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> StandortResponse:
    """Legt einen neuen Standort an (nur Admins)."""
    return crud_standort.create(db, payload)


@standorte_router.put("/{standort_id}", response_model=StandortResponse)
def update_standort(
    standort_id: int,
    payload: StandortUpdate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> StandortResponse:
    """Aktualisiert einen Standort (nur Admins)."""
    return crud_standort.update(db, standort_id, payload)


@standorte_router.delete("/{standort_id}", status_code=204)
def delete_standort(
    standort_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> None:
    """Löscht einen Standort (nur Admins)."""
    crud_standort.delete(db, standort_id)


# ---------------------------------------------------------------------------
# Boxen
# ---------------------------------------------------------------------------

@boxen_router.get("/", response_model=list[BoxResponse])
def list_boxen(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> list[BoxResponse]:
    """Gibt alle Boxen paginiert zurück."""
    return crud_box.get_all(db, skip=skip, limit=limit)


@boxen_router.get("/{box_id}", response_model=BoxResponse)
def get_box(
    box_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> BoxResponse:
    """Gibt eine einzelne Box anhand ihrer ID zurück."""
    return crud_box.get_by_id(db, box_id)


@boxen_router.post("/", response_model=BoxResponse, status_code=201)
def create_box(
    payload: BoxCreate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> BoxResponse:
    """Legt eine neue Box an (nur Admins)."""
    return crud_box.create(db, payload)


@boxen_router.put("/{box_id}", response_model=BoxResponse)
def update_box(
    box_id: int,
    payload: BoxUpdate,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> BoxResponse:
    """Aktualisiert eine Box (nur Admins)."""
    return crud_box.update(db, box_id, payload)


@boxen_router.delete("/{box_id}", status_code=204)
def delete_box(
    box_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> None:
    """Löscht eine Box (nur Admins)."""
    crud_box.delete(db, box_id)
