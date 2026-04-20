import enum

from app.db.base_class import Base

class GeraeteStatus(enum.Enum):
    VERFUEGBAR = "verfügbar"
    AUSGELIEHEN = "ausgeliehen"
    RESERVIERT = "reserviert"
    DEFEKT = "defekt"
    AUSSER_BETRIEB = "außer Betrieb"
    NICHT_VORHANDEN = "zur Zeit nicht vorhanden"

class BenutzerRolle(enum.Enum):
    STANDARD = "Studierende_Mitarbeitende"
    ADMIN = "Administrator"

class AusleihStatus(enum.Enum):
    AKTIV = "aktiv"
    UEBERFAELLIG = "überfällig"
    ABGESCHLOSSEN = "abgeschlossen"

class ReservierungsStatus(enum.Enum):
    AKTIV = "aktiv"
    ERFUELLT = "erfüllt"
    STORNIERT = "storniert"

class AktionType(enum.Enum):
    ANGELEGT = "angelegt"
    BEARBEITET = "bearbeitet"
    STATUS_AENDERUNG = "status_änderung"
    AUSLEIHE = "ausleihe"
    VERLAENGERUNG = "verlängerung"
    RUECKGABE = "rückgabe"
    RESERVIERUNG = "reservierung"
