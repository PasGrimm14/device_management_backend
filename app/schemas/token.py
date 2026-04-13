from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LocalLoginRequest(BaseModel):
    """Nur für lokales Testen – simuliert die Daten, die Shibboleth liefern würde."""
    shibboleth_id: str
    name: str
    email: str
