from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.base import AusleihStatus

from .geraet import GeraetResponse


class AusleiheCreate(BaseModel):
    """Payload, wenn ein Nutzer auf 'Ausleihen' klickt."""
    geraet_id: int
    geplantes_rueckgabedatum: Optional[datetime] = None


class RueckgabePayload(BaseModel):
    """Optionaler Body für den Rückgabe-Endpoint."""
    zustand_bei_rueckgabe: Optional[str] = None


class VerlaengerungPayload(BaseModel):
    """Payload für die Verlängerung – optionale Langzeit-Option."""
    langzeit: bool = False


class AusleiheResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    geraet_id: int
    nutzer_id: int
    startdatum: datetime
    geplantes_rueckgabedatum: datetime
    tatsaechliches_rueckgabedatum: Optional[datetime] = None
    status: AusleihStatus
    verlaengerungen_anzahl: int
    zustand_bei_rueckgabe: Optional[str] = None
    langzeit_verlaengerung_genutzt: bool = False
    geraet: Optional[GeraetResponse] = None


class AusleiheUeberfaelligResponse(AusleiheResponse):
    """Erweitertes Antwortschema für überfällige Ausleihen."""
    ueberfaellig_seit_tagen: int