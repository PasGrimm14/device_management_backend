from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.crud import geraet_bilder as crud
from app.models.benutzer import Benutzer
from app.schemas.geraet_bild import GeraetBildResponse, GeraetBildUrlResponse, GeraetBildZuweisen
from app.schemas.geraet import GeraetResponse

# POST /admin/bilder
upload_router = APIRouter()

# PUT /admin/geraete/{geraet_id}/bild
admin_geraet_bild_router = APIRouter()


@upload_router.post("/", response_model=GeraetBildResponse, status_code=201)
async def upload_bild(
    datei: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
):
    """Lädt ein neues Gerätebild hoch und gibt die neue bild_id zurück.

    Erlaubte Typen: JPEG, PNG, WebP · Maximale Größe: 5 MB
    """
    inhalt = await datei.read()
    return crud.upload(
        db,
        datei_inhalt=inhalt,
        original_dateiname=datei.filename or "upload",
        mime_type=datei.content_type or "",
        nutzer_id=admin.id,
    )


@admin_geraet_bild_router.put("/{geraet_id}/bild", response_model=GeraetResponse)
def assign_bild(
    geraet_id: int,
    payload: GeraetBildZuweisen,
    db: Session = Depends(get_db),
    admin: Benutzer = Depends(require_admin),
):
    """Weist einem Gerät ein bereits hochgeladenes Bild zu."""
    return crud.assign_bild(db, geraet_id, payload.bild_id, admin.id)
