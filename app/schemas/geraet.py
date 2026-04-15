from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import GeraeteStatus


class GeraetBase(BaseModel):

    inventar_nummer: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    kategorie: Optional[str] = Field(default=None, max_length=50)
    hersteller: Optional[str] = Field(default=None, max_length=50)
    modell: Optional[str] = Field(default=None, max_length=50)
    seriennummer: Optional[str] = Field(default=None, max_length=100)
    box_id: Optional[int] = None
    status: GeraeteStatus = GeraeteStatus.VERFUEGBAR
    anschaffungsdatum: Optional[date] = None
    bemerkungen: Optional[str] = None


class GeraetCreate(GeraetBase):
    """Payload für den Admin zum Anlegen eines neuen Geräts."""
    pass


class GeraetUpdate(BaseModel):
    """Erlaubt das partielle Aktualisieren von Geräten (PATCH)."""

    name: Optional[str] = Field(default=None, max_length=100)
    kategorie: Optional[str] = Field(default=None, max_length=50)
    hersteller: Optional[str] = Field(default=None, max_length=50)
    modell: Optional[str] = Field(default=None, max_length=50)
    seriennummer: Optional[str] = Field(default=None, max_length=100)
    box_id: Optional[int] = None
    status: Optional[GeraeteStatus] = None
    bemerkungen: Optional[str] = None


class GeraetResponse(GeraetBase):
    """Die Antwortstruktur, die das Frontend erhält."""
    id: int
    bild_id: Optional[int] = None
    qr_code_url: str

    model_config = ConfigDict(from_attributes=True)