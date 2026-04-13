import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.models.ausleihe import Ausleihe
from app.models.base import AusleihStatus

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def mark_ueberfaellige_ausleihen() -> None:
    """Setzt alle aktiven Ausleihen, deren Rückgabedatum überschritten ist, auf UEBERFAELLIG.

    Wird täglich um 01:00 Uhr UTC ausgeführt.
    """
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


def start_scheduler() -> None:
    scheduler.add_job(
        mark_ueberfaellige_ausleihen,
        trigger="cron",
        hour=1,
        minute=0,
        id="mark_ueberfaellig",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler gestartet – Überfälligkeits-Job läuft täglich um 01:00 UTC.")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler gestoppt.")
