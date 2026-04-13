from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.base import AktionType, BenutzerRolle, GeraeteStatus, ReservierungsStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet
from app.models.reservierung import Reservierung
from app.schemas.reservierung import ReservierungCreate


def get_all(db: Session, current_user: Benutzer, skip: int = 0, limit: int = 50) -> list[Reservierung]:
    q = db.query(Reservierung)
    if current_user.rolle != BenutzerRolle.ADMIN:
        q = q.filter(Reservierung.nutzer_id == current_user.id)
    return q.offset(skip).limit(limit).all()


def create(db: Session, payload: ReservierungCreate, current_user: Benutzer) -> Reservierung:
    geraet = db.get(Geraet, payload.geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    if geraet.status in (GeraeteStatus.DEFEKT, GeraeteStatus.AUSSER_BETRIEB):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gerät kann nicht reserviert werden (Status: {geraet.status.value}).",
        )

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


def stornieren(db: Session, reservierung_id: int, current_user: Benutzer) -> None:
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

    andere_reservierung = (
        db.query(Reservierung)
        .filter(
            Reservierung.geraet_id == reservierung.geraet_id,
            Reservierung.id != reservierung_id,
            Reservierung.status == ReservierungsStatus.AKTIV,
        )
        .first()
    )
    geraet = db.get(Geraet, reservierung.geraet_id)
    if geraet and geraet.status == GeraeteStatus.RESERVIERT and not andere_reservierung:
        geraet.status = GeraeteStatus.VERFUEGBAR

    db.commit()
