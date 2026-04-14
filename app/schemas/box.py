from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.standort import StandortResponse


class BoxBase(BaseModel):

    box_nummer: str | None = Field(default=None, max_length=50)
    standort_id: int
    beschreibung: str | None = None


class BoxCreate(BoxBase):
    """Payload zum Anlegen einer neuen Box."""
    pass


class BoxUpdate(BaseModel):
    """Erlaubt das partielle Aktualisieren einer Box (PUT)."""

    box_nummer: str | None = Field(default=None, max_length=50)
    standort_id: int | None = None
    beschreibung: str | None = None


class BoxResponse(BoxBase):
    """Antwortstruktur für eine Box (inkl. verschachteltem Standort)."""

    id: int
    standort: StandortResponse

    model_config = ConfigDict(from_attributes=True)
