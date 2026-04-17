import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.mail import send_mail
from app.db.session import SessionLocal
from app.models.ausleihe import Ausleihe
from app.models.base import AusleihStatus

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def mark_ueberfaellige_ausleihen() -> None:
    """Setzt alle aktiven Ausleihen, deren Rückgabedatum überschritten ist, auf UEBERFAELLIG."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        betroffene = (
            db.query(Ausleihe)
            .filter(
                Ausleihe.status == AusleihStatus.AKTIV,
                Ausleihe.geplantes_rueckgabedatum < now,
            )
            .all()
        )
        if not betroffene:
            return
        for ausleihe in betroffene:
            ausleihe.status = AusleihStatus.UEBERFAELLIG
        db.commit()
        logger.info("%d Ausleihe(n) als überfällig markiert.", len(betroffene))
    except Exception:
        db.rollback()
        logger.exception("Fehler beim Markieren überfälliger Ausleihen.")
    finally:
        db.close()


def send_erinnerungen() -> None:
    """Sendet Frist-Erinnerungen für Ausleihen, deren Rückgabe morgen oder übermorgen fällig ist."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        morgen = now + timedelta(days=1)
        uebermorgen = now + timedelta(days=2)
        betroffene = (
            db.query(Ausleihe)
            .filter(
                Ausleihe.status == AusleihStatus.AKTIV,
                Ausleihe.geplantes_rueckgabedatum >= morgen,
                Ausleihe.geplantes_rueckgabedatum < uebermorgen + timedelta(days=1),
                Ausleihe.erinnerung_gesendet.is_(False),
            )
            .all()
        )
        if not betroffene:
            return
        for ausleihe in betroffene:
            nutzer = ausleihe.nutzer
            geraet = ausleihe.geraet
            rueckgabe = ausleihe.geplantes_rueckgabedatum.date()
            send_mail(
                to=nutzer.email,
                subject=f"Erinnerung: Rückgabe von '{geraet.name}' am {rueckgabe}",
                body=(
                    f"Hallo {nutzer.name},\n\n"
                    f"dies ist eine Erinnerung, dass Sie das Gerät '{geraet.name}' "
                    f"(Inventarnummer: {geraet.inventar_nummer}) bis zum {rueckgabe} zurückgeben müssen.\n\n"
                    "Bitte geben Sie das Gerät fristgerecht zurück.\n\n"
                    "Mit freundlichen Grüßen\nDHBW Geräteverwaltung"
                ),
            )
            ausleihe.erinnerung_gesendet = True
        db.commit()
        logger.info("%d Erinnerung(en) versendet.", len(betroffene))
    except Exception:
        db.rollback()
        logger.exception("Fehler beim Versenden von Erinnerungen.")
    finally:
        db.close()


def send_mahnungen() -> None:
    """Sendet Mahnungen für überfällige Ausleihen, bei denen noch keine Mahnung versendet wurde."""
    db = SessionLocal()
    try:
        betroffene = (
            db.query(Ausleihe)
            .filter(
                Ausleihe.status == AusleihStatus.UEBERFAELLIG,
                Ausleihe.mahnung_gesendet.is_(False),
            )
            .all()
        )
        if not betroffene:
            return
        for ausleihe in betroffene:
            nutzer = ausleihe.nutzer
            geraet = ausleihe.geraet
            faellig_seit = ausleihe.geplantes_rueckgabedatum.date()
            send_mail(
                to=nutzer.email,
                subject=f"Mahnung: Gerät '{geraet.name}' überfällig seit {faellig_seit}",
                body=(
                    f"Hallo {nutzer.name},\n\n"
                    f"das Gerät '{geraet.name}' (Inventarnummer: {geraet.inventar_nummer}) "
                    f"war am {faellig_seit} zur Rückgabe fällig und wurde bisher nicht zurückgegeben.\n\n"
                    "Bitte geben Sie das Gerät umgehend zurück oder kontaktieren Sie uns.\n\n"
                    "Mit freundlichen Grüßen\nDHBW Geräteverwaltung"
                ),
            )
            ausleihe.mahnung_gesendet = True
        db.commit()
        logger.info("%d Mahnung(en) versendet.", len(betroffene))
    except Exception:
        db.rollback()
        logger.exception("Fehler beim Versenden von Mahnungen.")
    finally:
        db.close()


def ablauf_reservierungen_pruefen() -> None:
    """Setzt Reservierungen, deren Ablaufdatum überschritten ist, auf STORNIERT
    und gibt das Gerät wieder als verfügbar frei. Täglich um 01:15 UTC."""
    # Import hier um zirkuläre Imports zu vermeiden
    from app.crud.reservierungen import ablauf_pruefen
    db = SessionLocal()
    try:
        anzahl = ablauf_pruefen(db)
        if anzahl:
            logger.info("%d abgelaufene Reservierung(en) storniert.", anzahl)
    except Exception:
        logger.exception("Fehler beim Prüfen abgelaufener Reservierungen.")
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        mark_ueberfaellige_ausleihen,
        trigger="cron",
        hour=1, minute=0,
        id="mark_ueberfaellig",
        replace_existing=True,
    )
    scheduler.add_job(
        ablauf_reservierungen_pruefen,
        trigger="cron",
        hour=1, minute=15,
        id="ablauf_reservierungen",
        replace_existing=True,
    )
    scheduler.add_job(
        send_erinnerungen,
        trigger="cron",
        hour=8, minute=0,
        id="send_erinnerungen",
        replace_existing=True,
    )
    scheduler.add_job(
        send_mahnungen,
        trigger="cron",
        hour=8, minute=0,
        id="send_mahnungen",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler gestartet – Überfälligkeits-Job 01:00 UTC, "
        "Reservierungs-Ablauf-Job 01:15 UTC, "
        "Erinnerungs- und Mahnungs-Jobs 08:00 UTC."
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler gestoppt.")
