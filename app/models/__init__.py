# 1. Zuerst das Base und die Enums laden
from .base import Base, GeraeteStatus, BenutzerRolle, AusleihStatus, ReservierungsStatus, AktionType

# 2. Dann alle Tabellen-Modelle laden, damit sie an das Base gebunden werden
from .benutzer import Benutzer
from .geraet_bild import GeraetBild
from .geraet import Geraet
from .ausleihe import Ausleihe
from .reservierung import Reservierung
from .audit_log import AuditLog

# Optional, aber Best Practice: Definiert, was beim Importieren mit * geladen wird
__all__ = [
    "Base",
    "GeraeteStatus",
    "BenutzerRolle",
    "AusleihStatus",
    "ReservierungsStatus",
    "AktionType",
    "Benutzer",
    "GeraetBild",
    "Geraet",
    "Ausleihe",
    "Reservierung",
    "AuditLog",
]