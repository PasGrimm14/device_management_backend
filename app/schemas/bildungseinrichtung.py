from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BildungseinrichtungBase(BaseModel):

    name: str = Field(..., max_length=255)
    strasse: str | None = Field(default=None, max_length=255)
    hausnummer: str | None = Field(default=None, max_length=20)
    plz: str | None = Field(default=None, max_length=10)
    ort: str | None = Field(default=None, max_length=255)
    bundesland: str | None = Field(default=None, max_length=255)


class BildungseinrichtungCreate(BildungseinrichtungBase):
    """Payload zum Anlegen einer neuen Bildungseinrichtung."""
    pass


class BildungseinrichtungUpdate(BaseModel):
    """Erlaubt das partielle Aktualisieren einer Bildungseinrichtung (PUT)."""

    name: str | None = Field(default=None, max_length=255)
    strasse: str | None = Field(default=None, max_length=255)
    hausnummer: str | None = Field(default=None, max_length=20)
    plz: str | None = Field(default=None, max_length=10)
    ort: str | None = Field(default=None, max_length=255)
    bundesland: str | None = Field(default=None, max_length=255)


class BildungseinrichtungResponse(BildungseinrichtungBase):
    """Antwortstruktur für eine Bildungseinrichtung."""

    id: int

    model_config = ConfigDict(from_attributes=True)
