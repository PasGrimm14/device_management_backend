from __future__ import annotations

import io
import re

import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import geraete as crud
from app.models.benutzer import Benutzer
from app.schemas.qr_nfc import NfcPayloadResponse, NfcResolveRequest, NfcResolveResponse

# Regulärer Ausdruck zum Extrahieren der Geräte-ID aus einer NFC/QR-URL.
# Erwartet Format: <beliebige Basis>/geraete/<id>
_GERAET_ID_RE = re.compile(r"/geraete/(\d+)$")

# Zwei separate Router, da sie unter verschiedenen Präfixen eingebunden werden:
#   geraet_router → /geraete
#   nfc_router    → /nfc
geraet_router = APIRouter()
nfc_router = APIRouter()


# ---------------------------------------------------------------------------
# QR-Code
# ---------------------------------------------------------------------------

@geraet_router.get(
    "/{geraet_id}/qr-code",
    summary="QR-Code für ein Gerät generieren",
    responses={
        200: {"content": {"image/png": {}, "image/svg+xml": {}}},
        404: {"description": "Gerät nicht gefunden"},
    },
)
def get_qr_code(
    geraet_id: int,
    format: str = Query(default="png", pattern="^(png|svg)$", description="Ausgabeformat: png oder svg"),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> StreamingResponse:
    """Gibt einen QR-Code für die eindeutige Geräte-URL zurück.

    Die encodierte URL stammt aus der `qr_code_url`-Property des Geräts
    (`{BASE_URL}/geraete/{id}`) – die Logik wird nicht dupliziert.

    - **format=png** (Standard): Rasterbasiertes PNG-Bild
    - **format=svg**: Vektorbasiertes SVG (skalierbar, druckoptimiert)
    """
    geraet = crud.get_by_id(db, geraet_id)

    buf = io.BytesIO()

    if format == "svg":
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(geraet.qr_code_url, image_factory=factory)
        img.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/svg+xml")

    # PNG (Standard)
    img = qrcode.make(geraet.qr_code_url)
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# ---------------------------------------------------------------------------
# NFC-Payload
# ---------------------------------------------------------------------------

@geraet_router.get(
    "/{geraet_id}/nfc-payload",
    response_model=NfcPayloadResponse,
    summary="NFC NDEF-Payload für ein Gerät abrufen",
    responses={404: {"description": "Gerät nicht gefunden"}},
)
def get_nfc_payload(
    geraet_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> NfcPayloadResponse:
    """Gibt die NFC-Tag-Schreibdaten für ein Gerät zurück.

    `ndef_uri_record` enthält die volle URI, die in einen NDEF URI Record
    (TNF 0x01, Type "U") eingebettet werden soll. Das Frontend oder ein
    NFC-Schreibtool kann diesen Wert direkt verwenden.
    """
    geraet = crud.get_by_id(db, geraet_id)
    url = geraet.qr_code_url
    return NfcPayloadResponse(
        geraet_id=geraet.id,
        url=url,
        ndef_uri_record=url,
    )


# ---------------------------------------------------------------------------
# NFC-Resolve
# ---------------------------------------------------------------------------

@nfc_router.post(
    "/resolve",
    response_model=NfcResolveResponse,
    summary="NFC-URL zu Gerätedaten auflösen",
    responses={404: {"description": "URL-Format ungültig oder Gerät nicht gefunden"}},
)
def resolve_nfc_url(
    payload: NfcResolveRequest,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> NfcResolveResponse:
    """Löst eine vom NFC-Tag ausgelesene URL zu den Gerätegrunddaten auf.

    Erwartet eine URL im Format `{BASE_URL}/geraete/{id}`.
    Gibt HTTP 404 zurück, wenn das URL-Format nicht erkannt wird oder
    kein Gerät mit der extrahierten ID existiert.
    """
    match = _GERAET_ID_RE.search(payload.url)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL-Format ungültig oder Gerät nicht gefunden.",
        )

    geraet_id = int(match.group(1))
    geraet = crud.get_by_id(db, geraet_id)
    return NfcResolveResponse.model_validate(geraet)
