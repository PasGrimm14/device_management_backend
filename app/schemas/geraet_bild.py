from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GeraetBildResponse(BaseModel):
    """Die Antwortstruktur nach dem Upload eines Gerätebilds."""

    id: int
    dateiname: str
    mime_type: str
    hochgeladen_am: datetime

    model_config = ConfigDict(from_attributes=True)


class GeraetBildZuweisen(BaseModel):
    """Payload zum Zuweisen eines vorhandenen Bilds an ein Gerät."""

    bild_id: int


class GeraetBildUrlResponse(BaseModel):
    """Gibt eine zeitlich begrenzte URL zum Abrufen des Gerätebilds zurück."""

    presigned_url: str
