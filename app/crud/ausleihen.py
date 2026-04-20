from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.mail import send_mail
from app.models.audit_log import AuditLog
from app.models.ausleihe import Ausleihe
from app.models.base import AktionType, AusleihStatus, BenutzerRolle, GeraeteStatus, ReservierungsStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet
from app.models.reservierung import Reservierung
from app.schemas.ausleihe import AusleiheCreate

VERLAENGERUNG_TAGE = 14
VERLAENGERUNG_LANGZEIT_TAGE = 80
MAX_VERLAENGERUNGEN = 2


def get_all(db: Session, current_user: Benutzer, skip: int = 0, limit: int = 50) -> list[Ausleihe]:
    q = db.query(Ausleihe)
    if current_user.rolle != BenutzerRolle.ADMIN:
        q = q.filter(Ausleihe.nutzer_id == current_user.id)
    return q.offset(skip).limit(limit).all()


def get_by_id(db: Session, ausleihe_id: int, current_user: Benutzer) -> Ausleihe:
    ausleihe = db.get(Ausleihe, ausleihe_id)
    if ausleihe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausleihe nicht gefunden.")
    if current_user.rolle != BenutzerRolle.ADMIN and ausleihe.nutzer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff.")
    return ausleihe


def create(db: Session, payload: AusleiheCreate, current_user: Benutzer) -> Ausleihe:
    geraet = db.get(Geraet, payload.geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")

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
    db.add(AuditLog(
        nutzer_id=current_user.id,
        geraet_id=geraet.id,
        aktion=AktionType.AUSLEIHE,
        details=f"Gerät '{geraet.name}' ausgeliehen bis {rueckgabe.date()}.",
    ))
    db.commit()
    db.refresh(ausleihe)

    send_mail(
        to=current_user.email,
        subject=f"DHBW-Geräteverwaltung: Ausleihe bestätigt - {geraet.name}",
        body=(
            f"Hallo {current_user.name},\n\n"
            f"Ihre Ausleihe wurde erfolgreich erfasst.\n\n"
            f"Gerät:             {geraet.name}\n"
            f"Inventarnummer:    {geraet.inventar_nummer}\n"
            f"Ausgeliehen am:    {now.strftime('%d.%m.%Y')}\n"
            f"Rückgabe bis:      {rueckgabe.strftime('%d.%m.%Y')}\n\n"
            f"Bitte geben Sie das Gerät fristgerecht zurück.\n"
            f"Bei Fragen wenden Sie sich an das DHBW-Team.\n\n"
            f"Mit freundlichen Grüßen\n"
            f"DHBW Heilbronn – Geräteverwaltung"
        ),
    )

    return ausleihe


def verlaengern(
    db: Session,
    ausleihe_id: int,
    current_user: Benutzer,
    langzeit: bool = False,
) -> Ausleihe:
    """Verlängert eine Ausleihe.

    Bei langzeit=True und aktiviertem Langzeit-Flag am Gerät wird die Ausleihe
    um 80 Tage verlängert (nur eine solche Verlängerung möglich).
    Normale Verlängerungen: 14 Tage, max. 2×.
    """
    ausleihe = get_by_id(db, ausleihe_id, current_user)
    if ausleihe.status not in (AusleihStatus.AKTIV, AusleihStatus.UEBERFAELLIG):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nur aktive oder überfällige Ausleihen können verlängert werden.",
        )

    fremde_reservierung = (
        db.query(Reservierung)
        .filter(
            Reservierung.geraet_id == ausleihe.geraet_id,
            Reservierung.status == ReservierungsStatus.AKTIV,
            Reservierung.nutzer_id != current_user.id,
        )
        .first()
    )
    if fremde_reservierung:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Verlängerung nicht möglich – Gerät ist von einer anderen Person reserviert.",
        )

    geraet = db.get(Geraet, ausleihe.geraet_id)

    if langzeit:
        # Langzeit-Verlängerung: nur wenn Admin-Flag gesetzt und noch nicht genutzt
        if not geraet or not geraet.langzeit_ausleihe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Langzeit-Verlängerung für dieses Gerät nicht freigeschaltet.",
            )
        if ausleihe.langzeit_verlaengerung_genutzt:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Die Langzeit-Verlängerung (80 Tage) wurde bereits genutzt.",
            )
        ausleihe.geplantes_rueckgabedatum += timedelta(days=VERLAENGERUNG_LANGZEIT_TAGE)
        ausleihe.langzeit_verlaengerung_genutzt = True
        ausleihe.verlaengerungen_anzahl += 1
        tage = VERLAENGERUNG_LANGZEIT_TAGE
    else:
        if ausleihe.verlaengerungen_anzahl >= MAX_VERLAENGERUNGEN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Maximale Anzahl an Verlängerungen ({MAX_VERLAENGERUNGEN}) bereits erreicht.",
            )
        ausleihe.geplantes_rueckgabedatum += timedelta(days=VERLAENGERUNG_TAGE)
        ausleihe.verlaengerungen_anzahl += 1
        tage = VERLAENGERUNG_TAGE

    db.add(AuditLog(
        nutzer_id=current_user.id,
        geraet_id=ausleihe.geraet_id,
        aktion=AktionType.VERLAENGERUNG,
        details=f"Verlängerung #{ausleihe.verlaengerungen_anzahl} ({tage} Tage), "
                f"neues Rückgabedatum: {ausleihe.geplantes_rueckgabedatum.date()}.",
    ))
    db.commit()
    db.refresh(ausleihe)
    return ausleihe


def rueckgabe(
    db: Session,
    ausleihe_id: int,
    current_user: Benutzer,
    zustand: str | None = None,
) -> Ausleihe:
    ausleihe = get_by_id(db, ausleihe_id, current_user)
    if ausleihe.status not in (AusleihStatus.AKTIV, AusleihStatus.UEBERFAELLIG):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diese Ausleihe ist bereits abgeschlossen.",
        )

    now = datetime.now(timezone.utc)
    ausleihe.tatsaechliches_rueckgabedatum = now
    ausleihe.status = AusleihStatus.ABGESCHLOSSEN

    if zustand:
        ausleihe.zustand_bei_rueckgabe = zustand

    geraet = db.get(Geraet, ausleihe.geraet_id)

    if zustand:
        geraet.status = GeraeteStatus.DEFEKT
        db.add(AuditLog(
            nutzer_id=current_user.id,
            geraet_id=geraet.id,
            aktion=AktionType.STATUS_AENDERUNG,
            details=f"Gerät '{geraet.name}' bei Rückgabe als defekt gemeldet: {zustand}",
        ))
    else:
        offene_reservierung = (
            db.query(Reservierung)
            .filter(
                Reservierung.geraet_id == ausleihe.geraet_id,
                Reservierung.status == ReservierungsStatus.AKTIV,
            )
            .first()
        )
        geraet.status = GeraeteStatus.RESERVIERT if offene_reservierung else GeraeteStatus.VERFUEGBAR

    db.add(AuditLog(
        nutzer_id=current_user.id,
        geraet_id=ausleihe.geraet_id,
        aktion=AktionType.RUECKGABE,
        details=f"Gerät '{geraet.name}' zurückgegeben. Neuer Status: {geraet.status.value}.",
    ))
    db.commit()
    db.refresh(ausleihe)
    return ausleihe