from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.base import ReservierungsStatus

from .geraet import GeraetResponse


class ReservierungCreate(BaseModel):
    """Payload, wenn ein Nutzer ein Gerät reserviert.
    nutzer_id wird serverseitig aus dem Auth-Token ermittelt.
    """
    geraet_id: int
    reserviert_fuer_datum: date


class ReservierungResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    geraet_id: int
    nutzer_id: int
    erstellt_am: datetime
    reserviert_fuer_datum: date
    status: ReservierungsStatus
    geraet: Optional[GeraetResponse] = None
