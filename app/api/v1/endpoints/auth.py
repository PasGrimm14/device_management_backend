from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token
from app.models.benutzer import Benutzer
from app.models.base import BenutzerRolle
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
    In Produktion wird er durch den echten SSO-Callback ersetzt.
    """
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
