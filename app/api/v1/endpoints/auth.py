from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.base import BenutzerRolle
from app.models.benutzer import Benutzer
from app.schemas.benutzer import BenutzerResponse
from app.schemas.token import LocalLoginRequest, TokenResponse

router = APIRouter()


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Lokaler Test-Login (simuliert Shibboleth)",
)
def local_login(payload: LocalLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Legt den Benutzer an, falls er noch nicht existiert, und gibt ein JWT zurück.

    Dieser Endpoint ersetzt im lokalen Testbetrieb die Shibboleth-Weiterleitung.
    In Produktion wird er durch den echten SSO-Callback ersetzt und ist deshalb
    deaktiviert – Anfragen werden mit HTTP 403 abgewiesen.
    """
    if settings.ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local login disabled in production.",
        )

    benutzer = (
        db.query(Benutzer)
        .filter(Benutzer.shibboleth_id == payload.shibboleth_id)
        .first()
    )

    if benutzer is None:
        # Erster Benutzer in der DB wird automatisch Administrator
        ist_erster = db.query(Benutzer).first() is None
        rolle = BenutzerRolle.ADMIN if ist_erster else BenutzerRolle.STANDARD

        benutzer = Benutzer(
            shibboleth_id=payload.shibboleth_id,
            name=payload.name,
            email=payload.email,
            rolle=rolle,
        )
        db.add(benutzer)
        db.commit()
        db.refresh(benutzer)

    token = create_access_token(
        subject=benutzer.id,
        rolle=benutzer.rolle.value,
    )
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=BenutzerResponse,
    summary="Gibt den aktuell eingeloggten Benutzer zurück",
)
def read_current_user(
    current_user: Benutzer = Depends(get_current_user),
) -> BenutzerResponse:
    """Liefert Profildaten des authentifizierten Benutzers.

    Erwartet einen gültigen Bearer-Token im Authorization-Header.
    Gibt HTTP 401 zurück, wenn der Token fehlt, abgelaufen oder ungültig ist.
    """
    return current_user
