from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.mail import send_mail
from app.models.audit_log import AuditLog
from app.models.ausleihe import Ausleihe
from app.models.base import AktionType, AusleihStatus, BenutzerRolle, GeraeteStatus, ReservierungsStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet
from app.models.reservierung import Reservierung, RESERVIERUNG_ABLAUF_TAGE
from app.schemas.reservierung import ReservierungCreate

SEKRETARIAT_EMAIL = "sekretariat@dhbw-heilbronn.de"


def get_all(db: Session, current_user: Benutzer, skip: int = 0, limit: int = 50) -> list[Reservierung]:
    q = db.query(Reservierung)
    if current_user.rolle != BenutzerRolle.ADMIN:
        q = q.filter(Reservierung.nutzer_id == current_user.id)
    return q.offset(skip).limit(limit).all()


def create(db: Session, payload: ReservierungCreate, current_user: Benutzer) -> Reservierung:
    geraet = db.get(Geraet, payload.geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    if geraet.status in (GeraeteStatus.DEFEKT, GeraeteStatus.AUSSER_BETRIEB, GeraeteStatus.NICHT_VORHANDEN):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gerät kann nicht reserviert werden (Status: {geraet.status.value}).",
        )

    # Prüfen ob bereits eine aktive Reservierung für dieses Gerät an diesem Datum existiert
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

    # Prüfen ob das Gerät an diesem Datum noch ausgeliehen ist (aktive Ausleihe mit Rückgabedatum nach Abholdatum)
    # Das geplante Abholdatum als datetime am Tagesbeginn
    abhol_datetime = datetime(
        payload.reserviert_fuer_datum.year,
        payload.reserviert_fuer_datum.month,
        payload.reserviert_fuer_datum.day,
        tzinfo=timezone.utc,
    )
    # Ende des Abholdatums (23:59 UTC)
    abhol_datetime_end = abhol_datetime + timedelta(hours=23, minutes=59)

    aktive_ausleihe_im_zeitraum = (
        db.query(Ausleihe)
        .filter(
            Ausleihe.geraet_id == payload.geraet_id,
            Ausleihe.status.in_([AusleihStatus.AKTIV, AusleihStatus.UEBERFAELLIG]),
            # Ausleihe läuft noch am Abholtag: Rückgabedatum liegt NACH dem Beginn des Abholtags
            Ausleihe.geplantes_rueckgabedatum > abhol_datetime,
        )
        .first()
    )
    if aktive_ausleihe_im_zeitraum:
        rueckgabe_datum = aktive_ausleihe_im_zeitraum.geplantes_rueckgabedatum.strftime('%d.%m.%Y')
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Das Gerät ist voraussichtlich bis {rueckgabe_datum} ausgeliehen. "
                f"Bitte wählen Sie ein späteres Abholdatum."
            ),
        )

    now = datetime.now(timezone.utc)
    ablaufdatum = now + timedelta(days=RESERVIERUNG_ABLAUF_TAGE)

    reservierung = Reservierung(
        geraet_id=payload.geraet_id,
        nutzer_id=current_user.id,
        reserviert_fuer_datum=payload.reserviert_fuer_datum,
        ablaufdatum=ablaufdatum,
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
        details=f"Gerät '{geraet.name}' reserviert für {payload.reserviert_fuer_datum} (Ablauf: {ablaufdatum.date()}).",
    ))
    db.commit()
    db.refresh(reservierung)

    send_mail(
        to=current_user.email,
        subject=f"DHBW-Geräteverwaltung: Reservierung bestätigt – {geraet.name}",
        body=(
            f"Hallo {current_user.name},\n\n"
            f"Ihre Reservierung wurde erfolgreich erfasst.\n\n"
            f"Gerät:                    {geraet.name}\n"
            f"Inventarnummer:           {geraet.inventar_nummer}\n"
            f"Voraussichtliches Abholdatum: {payload.reserviert_fuer_datum.strftime('%d.%m.%Y')}\n"
            f"Automatischer Ablauf:     {ablaufdatum.strftime('%d.%m.%Y')}\n\n"
            f"Bitte holen Sie das Gerät rechtzeitig ab und scannen Sie den QR-Code, "
            f"um die Ausleihe zu starten.\n"
            f"Nicht abgeholte Reservierungen verfallen nach {RESERVIERUNG_ABLAUF_TAGE} Tagen automatisch.\n\n"
            f"Mit freundlichen Grüßen\n"
            f"DHBW Heilbronn – Geräteverwaltung"
        ),
    )

    send_mail(
        to=SEKRETARIAT_EMAIL,
        subject=f"Neue Reservierung: {geraet.name} – bitte vorbereiten",
        body=(
            f"Neue Gerätereservierung eingegangen:\n\n"
            f"Gerät:                    {geraet.name}\n"
            f"Inventarnummer:           {geraet.inventar_nummer}\n"
            f"Unique-Name:              {geraet.unique_name or '–'}\n"
            f"Kategorie:                {geraet.kategorie or '–'}\n"
            f"Reserviert von:           {current_user.name} ({current_user.email})\n"
            f"Voraussichtliches Abholdatum: {payload.reserviert_fuer_datum.strftime('%d.%m.%Y')}\n"
            f"Automatischer Ablauf:     {ablaufdatum.strftime('%d.%m.%Y')}\n\n"
            f"Bitte bereiten Sie das Gerät für die Abholung vor.\n"
            f"Die Ausleihe wird durch Scannen des QR-Codes am Gerät ausgelöst.\n\n"
            f"DHBW Heilbronn – Geräteverwaltung"
        ),
    )

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


def ablauf_pruefen(db: Session) -> int:
    """Setzt abgelaufene Reservierungen auf STORNIERT und gibt das Gerät frei."""
    now = datetime.now(timezone.utc)
    abgelaufene = (
        db.query(Reservierung)
        .filter(
            Reservierung.status == ReservierungsStatus.AKTIV,
            Reservierung.ablaufdatum.isnot(None),
            Reservierung.ablaufdatum < now,
        )
        .all()
    )
    if not abgelaufene:
        return 0

    for reservierung in abgelaufene:
        reservierung.status = ReservierungsStatus.STORNIERT
        geraet = db.get(Geraet, reservierung.geraet_id)
        if geraet and geraet.status == GeraeteStatus.RESERVIERT:
            andere = (
                db.query(Reservierung)
                .filter(
                    Reservierung.geraet_id == reservierung.geraet_id,
                    Reservierung.id != reservierung.id,
                    Reservierung.status == ReservierungsStatus.AKTIV,
                )
                .first()
            )
            if not andere:
                geraet.status = GeraeteStatus.VERFUEGBAR

    db.commit()
    return len(abgelaufene)