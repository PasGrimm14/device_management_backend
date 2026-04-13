from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_access_token(subject: int, rolle: str) -> str:
    """Erstellt ein signiertes JWT.

    Args:
        subject: Datenbankid des Benutzers (wird als 'sub' gespeichert).
        rolle:   Wert von BenutzerRolle (z. B. 'Administrator').
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(subject),
        "rolle": rolle,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Dekodiert und validiert ein JWT. Wirft jwt.PyJWTError bei Fehler."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
