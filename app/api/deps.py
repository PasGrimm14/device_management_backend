from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.benutzer import Benutzer
from app.models.base import BenutzerRolle

bearer_scheme = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Benutzer:
    """Liest den Bearer-Token, validiert ihn und gibt den Benutzer zurück."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ungültig oder abgelaufen.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_exception

    benutzer = db.get(Benutzer, user_id)
    if benutzer is None:
        raise credentials_exception
    return benutzer


def require_admin(
    current_user: Benutzer = Depends(get_current_user),
) -> Benutzer:
    """Wirft 403, wenn der eingeloggte Benutzer kein Administrator ist."""
    if current_user.rolle != BenutzerRolle.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren dürfen diese Aktion ausführen.",
        )
    return current_user
