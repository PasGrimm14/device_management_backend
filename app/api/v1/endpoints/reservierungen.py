from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.base import AktionType, BenutzerRolle, GeraeteStatus, ReservierungsStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet
from app.models.reservierung import Reservierung
from app.schemas.reservierung import ReservierungCreate, ReservierungResponse

router = APIRouter()


@router.get("/", response_model=list[ReservierungResponse])
def list_reservierungen(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> list[Reservierung]:
    """Admins sehen alle Reservierungen, normale Nutzer nur ihre eigenen."""
    q = db.query(Reservierung)
    if current_user.rolle != BenutzerRolle.ADMIN:
        q = q.filter(Reservierung.nutzer_id == current_user.id)
    return q.offset(skip).limit(limit).all()


@router.post("/", response_model=ReservierungResponse, status_code=status.HTTP_201_CREATED)
def create_reservierung(
    payload: ReservierungCreate,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> Reservierung:
    """Reserviert ein Gerät für ein bestimmtes Datum."""
    geraet = db.get(Geraet, payload.geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    if geraet.status == GeraeteStatus.DEFEKT or geraet.status == GeraeteStatus.AUSSER_BETRIEB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gerät kann nicht reserviert werden (Status: {geraet.status.value}).",
        )

    # Doppelte Reservierung für dasselbe Datum verhindern
    existiert = (
        db.query(Reservierung)
        .filter(
            Reservierung.geraet_id == payload.geraet_id,
            Reservierung.reserviert_fuer_datum == payload.reserviert_fuer_datum,
            Reservierung.status == ReservierungsStatus.AKTIV,
        )
        .first()
    )
    if existiert:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Für dieses Gerät besteht an diesem Datum bereits eine aktive Reservierung.",
        )

    reservierung = Reservierung(
        geraet_id=payload.geraet_id,
        nutzer_id=current_user.id,
        reserviert_fuer_datum=payload.reserviert_fuer_datum,
        status=ReservierungsStatus.AKTIV,
    )
    # Gerät als reserviert markieren, falls es gerade verfügbar ist
    if geraet.status == GeraeteStatus.VERFUEGBAR:
        geraet.status = GeraeteStatus.RESERVIERT

    db.add(reservierung)
    db.flush()
    db.add(AuditLog(
        nutzer_id=current_user.id,
        geraet_id=geraet.id,
        aktion=AktionType.RESERVIERUNG,
        details=f"Gerät '{geraet.name}' reserviert für {payload.reserviert_fuer_datum}.",
    ))
    db.commit()
    db.refresh(reservierung)
    return reservierung


@router.delete("/{reservierung_id}", status_code=status.HTTP_204_NO_CONTENT)
def storniere_reservierung(
    reservierung_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> None:
    """Storniert eine Reservierung. Eigene oder als Admin."""
    reservierung = db.get(Reservierung, reservierung_id)
    if reservierung is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservierung nicht gefunden.")
    if current_user.rolle != BenutzerRolle.ADMIN and reservierung.nutzer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff.")
    if reservierung.status != ReservierungsStatus.AKTIV:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nur aktive Reservierungen können storniert werden.",
        )

    reservierung.status = ReservierungsStatus.STORNIERT

    # Gerät zurück auf VERFUEGBAR setzen, wenn keine weitere aktive Reservierung besteht
    andere_reservierung = (
        db.query(Reservierung)
        .filter(
            Reservierung.geraet_id == reservierung.geraet_id,
            Reservierung.id != reservierung_id,
            Reservierung.status == ReservierungsStatus.AKTIV,
        )
        .first()
    )
    if nicht := db.get(Geraet, reservierung.geraet_id):
        if nicht.status == GeraeteStatus.RESERVIERT and not andere_reservierung:
            nicht.status = GeraeteStatus.VERFUEGBAR

    db.commit()
