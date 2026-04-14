from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.bildungseinrichtung import BildungseinrichtungResponse


class StandortBase(BaseModel):

    bildungseinrichtung_id: int
    gebaeude: str | None = Field(default=None, max_length=255)
    raum: str | None = Field(default=None, max_length=100)
    beschreibung: str | None = None


class StandortCreate(StandortBase):
    """Payload zum Anlegen eines neuen Standorts."""
    pass


class StandortUpdate(BaseModel):
    """Erlaubt das partielle Aktualisieren eines Standorts (PUT)."""

    bildungseinrichtung_id: int | None = None
    gebaeude: str | None = Field(default=None, max_length=255)
    raum: str | None = Field(default=None, max_length=100)
    beschreibung: str | None = None


class StandortResponse(StandortBase):
    """Antwortstruktur für einen Standort (inkl. verschachtelter Bildungseinrichtung)."""

    id: int
    bildungseinrichtung: BildungseinrichtungResponse

    model_config = ConfigDict(from_attributes=True)
