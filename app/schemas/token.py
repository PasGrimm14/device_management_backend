from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.base import BenutzerRolle


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LocalLoginRequest(BaseModel):
    """Nur für lokales Testen – simuliert die Daten, die Shibboleth liefern würde."""
    shibboleth_id: str
    name: str
    email: str


class TokenPayload(BaseModel):
    """Decodierter JWT-Payload. sub wird von PyJWT als String geliefert;
    Pydantic v2 coerced ihn im lax-Modus automatisch zu int."""
    sub: int
    rolle: str
    exp: datetime


class CurrentUser(BaseModel):
    """Eingeloggter Benutzer, aus dem JWT extrahiert – wird per Depends injiziert.
    from_attributes=True erlaubt zusätzlich die direkte Konstruktion aus einem
    Benutzer-ORM-Objekt, falls ein Endpunkt das benötigt."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    rolle: BenutzerRolle
