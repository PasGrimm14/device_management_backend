import io
import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.minio_client import ensure_bucket_exists, get_minio_client
from app.models.audit_log import AuditLog
from app.models.base import AktionType
from app.models.geraet import Geraet
from app.models.geraet_bild import GeraetBild


ERLAUBTE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_DATEIGROESSE = 5 * 1024 * 1024  # 5 MB


def upload(
    db: Session,
    datei_inhalt: bytes,
    original_dateiname: str,
    mime_type: str,
    nutzer_id: int,
) -> GeraetBild:
    """Lädt ein Bild zu MinIO hoch und legt einen DB-Eintrag an."""
    if mime_type not in ERLAUBTE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Dateityp '{mime_type}' nicht erlaubt. Erlaubt: JPEG, PNG, WebP.",
        )
    if len(datei_inhalt) > MAX_DATEIGROESSE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Datei überschreitet die maximale Größe von 5 MB.",
        )

    endung = original_dateiname.rsplit(".", 1)[-1].lower() if "." in original_dateiname else "bin"
    dateiname = f"{uuid.uuid4()}.{endung}"

    client = get_minio_client()
    ensure_bucket_exists(client)
    client.put_object(
        settings.MINIO_BUCKET,
        dateiname,
        io.BytesIO(datei_inhalt),
        length=len(datei_inhalt),
        content_type=mime_type,
    )

    bild = GeraetBild(dateiname=dateiname, mime_type=mime_type)
    db.add(bild)
    db.flush()
    db.add(AuditLog(
        nutzer_id=nutzer_id,
        geraet_id=None,
        aktion=AktionType.BEARBEITET,
        details=f"Bild '{dateiname}' hochgeladen.",
    ))
    db.commit()
    db.refresh(bild)
    return bild


def assign_bild(
    db: Session,
    geraet_id: int,
    bild_id: int,
    nutzer_id: int,
) -> Geraet:
    """Weist einem Gerät ein vorhandenes Bild zu."""
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")

    bild = db.get(GeraetBild, bild_id)
    if bild is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bild nicht gefunden.")

    geraet.bild_id = bild_id
    db.add(AuditLog(
        nutzer_id=nutzer_id,
        geraet_id=geraet.id,
        aktion=AktionType.BEARBEITET,
        details=f"Bild {bild_id} ('{bild.dateiname}') zugewiesen.",
    ))
    db.commit()
    db.refresh(geraet)
    return geraet


def get_presigned_url(db: Session, geraet_id: int) -> str:
    """Gibt eine Presigned-URL (1 Stunde) für das Bild des Geräts zurück."""
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    if geraet.bild_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diesem Gerät ist kein Bild zugewiesen.",
        )

    bild = db.get(GeraetBild, geraet.bild_id)
    client = get_minio_client()
    url = client.presigned_get_object(
        settings.MINIO_BUCKET,
        bild.dateiname,
        expires=timedelta(hours=1),
    )
    return url
