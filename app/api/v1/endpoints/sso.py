import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.base import BenutzerRolle
from app.models.benutzer import Benutzer

router = APIRouter()


class OttRequest(BaseModel):
    token: str


@router.post("/callback", summary="SSO: OTT gegen JWT tauschen")
async def sso_callback(payload: OttRequest, db: Session = Depends(get_db)):
    """
    Wird vom Device Management Frontend aufgerufen wenn ein User
    von dhbw_repo_device weitergeleitet wird.
    Validiert den OTT bei dhbw_repo_device und gibt ein JWT zurück.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                settings.SYNC_SSO_VERIFY_URL,
                json={"token": payload.token},
                headers={"X-SSO-Secret": settings.SYNC_SSO_SECRET},
                timeout=10.0,
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SSO-Dienst nicht erreichbar.",
            )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener SSO-Token.",
        )

    user_data = resp.json()

    # User anlegen oder aktualisieren
    shibboleth_id = user_data["shibboleth_id"]
    benutzer = db.query(Benutzer).filter(Benutzer.shibboleth_id == shibboleth_id).first()

    rolle = BenutzerRolle.ADMIN if user_data["rolle"] == "Administrator" else BenutzerRolle.STANDARD

    if benutzer is None:
        benutzer = Benutzer(
            shibboleth_id=shibboleth_id,
            name=user_data["name"],
            email=user_data["email"],
            rolle=rolle,
        )
        db.add(benutzer)
        db.commit()
        db.refresh(benutzer)
    else:
        # Rolle und Name immer aus sg-gerätemanagement übernehmen
        benutzer.rolle = rolle
        benutzer.name = user_data["name"]
        db.commit()
        db.refresh(benutzer)

    token = create_access_token(subject=benutzer.id, rolle=benutzer.rolle.value)
    return {"access_token": token, "token_type": "bearer"}