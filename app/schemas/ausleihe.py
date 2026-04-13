from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.base import AusleihStatus

from .geraet import GeraetResponse


class AusleiheCreate(BaseModel):
    """Payload, wenn ein Nutzer auf 'Ausleihen' klickt.
    nutzer_id wird serverseitig aus dem Auth-Token ermittelt.
    """
    geraet_id: int
    geplantes_rueckgabedatum: Optional[datetime] = None


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
    geraet: Optional[GeraetResponse] = None