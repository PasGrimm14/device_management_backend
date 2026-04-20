from fastapi import APIRouter, Depends
from app.api.deps import require_admin
from app.models.benutzer import Benutzer
from app.core.scheduler import (
    mark_ueberfaellige_ausleihen,
    send_erinnerungen,
    send_mahnungen,
    ablauf_reservierungen_pruefen,
)

router = APIRouter()

@router.post("/ueberfaellig", summary="Überfällige Ausleihen manuell prüfen")
def trigger_ueberfaellig(_: Benutzer = Depends(require_admin)):
    mark_ueberfaellige_ausleihen()
    return {"message": "Job 'mark_ueberfaellige_ausleihen' ausgeführt."}

@router.post("/erinnerungen", summary="Erinnerungen manuell senden")
def trigger_erinnerungen(_: Benutzer = Depends(require_admin)):
    send_erinnerungen()
    return {"message": "Job 'send_erinnerungen' ausgeführt."}

@router.post("/mahnungen", summary="Mahnungen manuell senden")
def trigger_mahnungen(_: Benutzer = Depends(require_admin)):
    send_mahnungen()
    return {"message": "Job 'send_mahnungen' ausgeführt."}

@router.post("/reservierungen-ablauf", summary="Abgelaufene Reservierungen manuell prüfen")
def trigger_reservierungen(_: Benutzer = Depends(require_admin)):
    anzahl = ablauf_reservierungen_pruefen()
    return {"message": f"Job 'ablauf_reservierungen' ausgeführt. {anzahl} Reservierung(en) storniert."}
