from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.ausleihe import Ausleihe
from app.models.base import AktionType, AusleihStatus, BenutzerRolle, GeraeteStatus, ReservierungsStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet
from app.models.reservierung import Reservierung
from app.schemas.ausleihe import AusleiheCreate, AusleiheResponse

router = APIRouter()

VERLAENGERUNG_TAGE = 14
MAX_VERLAENGERUNGEN = 2


def _write_audit(
    db: Session,
    nutzer_id: int,
    aktion: AktionType,
    geraet_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    db.add(AuditLog(nutzer_id=nutzer_id, geraet_id=geraet_id, aktion=aktion, details=details))


@router.get("/", response_model=list[AusleiheResponse])
def list_ausleihen(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> list[Ausleihe]:
    """Admins sehen alle Ausleihen, normale Nutzer nur ihre eigenen."""
    q = db.query(Ausleihe)
    if current_user.rolle != BenutzerRolle.ADMIN:
        q = q.filter(Ausleihe.nutzer_id == current_user.id)
    return q.offset(skip).limit(limit).all()


@router.get("/{ausleihe_id}", response_model=AusleiheResponse)
def get_ausleihe(
    ausleihe_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> Ausleihe:
    ausleihe = db.get(Ausleihe, ausleihe_id)
    if ausleihe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausleihe nicht gefunden.")
    if current_user.rolle != BenutzerRolle.ADMIN and ausleihe.nutzer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff.")
    return ausleihe


@router.post("/", response_model=AusleiheResponse, status_code=status.HTTP_201_CREATED)
def create_ausleihe(
    payload: AusleiheCreate,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> Ausleihe:
    """Leiht ein Gerät aus. Das Gerät muss den Status 'verfügbar' haben."""
    geraet = db.get(Geraet, payload.geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")

    # VERFUEGBAR: direkt ausleihbar.
    # RESERVIERT: nur ausleihbar wenn der aktuelle Nutzer selbst die Reservierung hält.
    eigene_reservierung = None
    if geraet.status == GeraeteStatus.RESERVIERT:
        eigene_reservierung = (
            db.query(Reservierung)
            .filter(
                Reservierung.geraet_id == geraet.id,
                Reservierung.nutzer_id == current_user.id,
                Reservierung.status == ReservierungsStatus.AKTIV,
            )
            .first()
        )
        if eigene_reservierung is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Gerät ist reserviert – nur der Reservierungsinhaber kann es ausleihen.",
            )
    elif geraet.status != GeraeteStatus.VERFUEGBAR:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gerät ist nicht verfügbar (aktueller Status: {geraet.status.value}).",
        )

    now = datetime.now(timezone.utc)
    rueckgabe = payload.geplantes_rueckgabedatum or now + timedelta(days=VERLAENGERUNG_TAGE)

    ausleihe = Ausleihe(
        geraet_id=geraet.id,
        nutzer_id=current_user.id,
        startdatum=now,
        geplantes_rueckgabedatum=rueckgabe,
        status=AusleihStatus.AKTIV,
    )
    geraet.status = GeraeteStatus.AUSGELIEHEN

    if eigene_reservierung:
        eigene_reservierung.status = ReservierungsStatus.ERFUELLT

    db.add(ausleihe)
    db.flush()
    _write_audit(
        db, current_user.id, AktionType.AUSLEIHE, geraet.id,
        f"Gerät '{geraet.name}' ausgeliehen bis {rueckgabe.date()}.",
    )
    db.commit()
    db.refresh(ausleihe)
    return ausleihe


@router.post("/{ausleihe_id}/verlaengern", response_model=AusleiheResponse)
def verlaengern(
    ausleihe_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> Ausleihe:
    """Verlängert eine aktive Ausleihe um 14 Tage (max. 2 Verlängerungen)."""
    ausleihe = db.get(Ausleihe, ausleihe_id)
    if ausleihe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausleihe nicht gefunden.")
    if current_user.rolle != BenutzerRolle.ADMIN and ausleihe.nutzer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff.")
    if ausleihe.status != AusleihStatus.AKTIV:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nur aktive Ausleihen können verlängert werden.",
        )
    if ausleihe.verlaengerungen_anzahl >= MAX_VERLAENGERUNGEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Maximale Anzahl an Verlängerungen ({MAX_VERLAENGERUNGEN}) bereits erreicht.",
        )

    ausleihe.geplantes_rueckgabedatum += timedelta(days=VERLAENGERUNG_TAGE)
    ausleihe.verlaengerungen_anzahl += 1
    _write_audit(
        db, current_user.id, AktionType.VERLAENGERUNG, ausleihe.geraet_id,
        f"Verlängerung #{ausleihe.verlaengerungen_anzahl}, "
        f"neues Rückgabedatum: {ausleihe.geplantes_rueckgabedatum.date()}.",
    )
    db.commit()
    db.refresh(ausleihe)
    return ausleihe


@router.post("/{ausleihe_id}/rueckgabe", response_model=AusleiheResponse)
def rueckgabe(
    ausleihe_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> Ausleihe:
    """Schließt eine Ausleihe ab und setzt den Gerätestatus zurück."""
    ausleihe = db.get(Ausleihe, ausleihe_id)
    if ausleihe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausleihe nicht gefunden.")
    if current_user.rolle != BenutzerRolle.ADMIN and ausleihe.nutzer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff.")
    if ausleihe.status not in (AusleihStatus.AKTIV, AusleihStatus.UEBERFAELLIG):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diese Ausleihe ist bereits abgeschlossen.",
        )

    now = datetime.now(timezone.utc)
    ausleihe.tatsaechliches_rueckgabedatum = now
    ausleihe.status = AusleihStatus.ABGESCHLOSSEN

    # Prüfen ob eine aktive Reservierung vorliegt → dann RESERVIERT, sonst VERFUEGBAR
    from app.models.reservierung import Reservierung
    from app.models.base import ReservierungsStatus
    offene_reservierung = (
        db.query(Reservierung)
        .filter(
            Reservierung.geraet_id == ausleihe.geraet_id,
            Reservierung.status == ReservierungsStatus.AKTIV,
        )
        .first()
    )
    geraet = db.get(Geraet, ausleihe.geraet_id)
    geraet.status = GeraeteStatus.RESERVIERT if offene_reservierung else GeraeteStatus.VERFUEGBAR

    _write_audit(
        db, current_user.id, AktionType.RUECKGABE, ausleihe.geraet_id,
        f"Gerät '{geraet.name}' zurückgegeben. Neuer Status: {geraet.status.value}.",
    )
    db.commit()
    db.refresh(ausleihe)
    return ausleihe
