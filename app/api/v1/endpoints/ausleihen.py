from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.crud import ausleihen as crud
from app.models.ausleihe import Ausleihe
from app.models.base import AusleihStatus
from app.models.benutzer import Benutzer
from app.schemas.ausleihe import AusleiheCreate, AusleiheResponse, AusleiheUeberfaelligResponse, RueckgabePayload, VerlaengerungPayload

router = APIRouter()


@router.get("/ueberfaellig", response_model=list[AusleiheUeberfaelligResponse])
def list_ueberfaellige_ausleihen(
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    ausleihen = (
        db.query(Ausleihe)
        .filter(Ausleihe.status == AusleihStatus.UEBERFAELLIG)
        .order_by(Ausleihe.geplantes_rueckgabedatum.asc())
        .all()
    )
    now = datetime.now(timezone.utc)
    result = []
    for ausleihe in ausleihen:
        tage = (now - ausleihe.geplantes_rueckgabedatum).days
        base = AusleiheResponse.model_validate(ausleihe).model_dump()
        base["ueberfaellig_seit_tagen"] = tage
        result.append(AusleiheUeberfaelligResponse(**base))
    return result


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
    payload: VerlaengerungPayload = Body(default_factory=VerlaengerungPayload),
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.verlaengern(db, ausleihe_id, current_user, langzeit=payload.langzeit)


@router.post("/{ausleihe_id}/rueckgabe", response_model=AusleiheResponse)
def rueckgabe(
    ausleihe_id: int,
    payload: RueckgabePayload = Body(default_factory=RueckgabePayload),
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
):
    return crud.rueckgabe(db, ausleihe_id, current_user, zustand=payload.zustand_bei_rueckgabe)