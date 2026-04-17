from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.base import ReservierungsStatus

from .geraet import GeraetResponse


class ReservierungCreate(BaseModel):
    geraet_id: int
    reserviert_fuer_datum: date


class ReservierungResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    geraet_id: int
    nutzer_id: int
    erstellt_am: datetime
    reserviert_fuer_datum: date
    ablaufdatum: Optional[datetime] = None
    status: ReservierungsStatus
    geraet: Optional[GeraetResponse] = None
