from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import GeraeteStatus


class GeraetBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    inventar_nummer: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    kategorie: Optional[str] = Field(default=None, max_length=50)
    hersteller: Optional[str] = Field(default=None, max_length=50)
    modell: Optional[str] = Field(default=None, max_length=50)
    seriennummer: Optional[str] = Field(default=None, max_length=100)
    standort: Optional[str] = Field(default=None, max_length=100)
    status: GeraeteStatus = GeraeteStatus.VERFUEGBAR
    anschaffungsdatum: Optional[date] = None
    bemerkungen: Optional[str] = None


class GeraetCreate(GeraetBase):
    """Payload für den Admin zum Anlegen eines neuen Geräts."""
    pass


class GeraetUpdate(BaseModel):
    """Erlaubt das partielle Aktualisieren von Geräten (PATCH)."""
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(default=None, max_length=100)
    standort: Optional[str] = Field(default=None, max_length=100)
    status: Optional[GeraeteStatus] = None
    bemerkungen: Optional[str] = None


class GeraetResponse(GeraetBase):
    """Die Antwortstruktur, die das Frontend erhält."""
    id: int
    qr_code_url: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)