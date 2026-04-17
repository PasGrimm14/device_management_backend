from __future__ import annotations

import io
import re

import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import ausleihen as crud_ausleihen
from app.crud import geraete as crud
from app.models.benutzer import Benutzer
from app.schemas.ausleihe import AusleiheCreate, AusleiheResponse
from app.schemas.qr_nfc import NfcPayloadResponse, NfcResolveRequest, NfcResolveResponse

_GERAET_ID_RE = re.compile(r"/geraete/(\d+)$")

geraet_router = APIRouter()
nfc_router = APIRouter()


# ---------------------------------------------------------------------------
# QR-Code (nur Admin-Download; nicht mehr in der User-UI sichtbar)
# ---------------------------------------------------------------------------

@geraet_router.get(
    "/{geraet_id}/qr-code",
    summary="QR-Code für ein Gerät generieren (mit Unique-Name-Beschriftung)",
    responses={
        200: {"content": {"image/png": {}, "image/svg+xml": {}}},
        404: {"description": "Gerät nicht gefunden"},
    },
)
def get_qr_code(
    geraet_id: int,
    format: str = Query(default="png", pattern="^(png|svg)$"),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> StreamingResponse:
    """Gibt einen QR-Code zurück.

    Bei PNG wird der unique_name des Geräts unter dem QR-Code eingedruckt,
    sodass der Ausdruck eindeutig identifizierbar ist.
    """
    geraet = crud.get_by_id(db, geraet_id)
    buf = io.BytesIO()

    if format == "svg":
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(geraet.qr_code_url, image_factory=factory)
        img.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/svg+xml")

    # PNG mit Beschriftung
    qr_img = qrcode.make(geraet.qr_code_url)
    qr_img = qr_img.convert("RGB")

    label = geraet.unique_name or geraet.inventar_nummer
    label_secondary = geraet.name

    # Weißen Bereich unter dem QR-Code für den Text ergänzen
    qr_w, qr_h = qr_img.size
    padding = 12
    text_area_h = 48
    new_h = qr_h + text_area_h + padding
    final_img = Image.new("RGB", (qr_w, new_h), "white")
    final_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(final_img)

    # Schriftgröße: Pillow-Default ohne externe Fonts
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except (IOError, OSError):
        font_main = ImageFont.load_default()
        font_sub = font_main

    # Unique-Name zentriert
    bbox_main = draw.textbbox((0, 0), label, font=font_main)
    w_main = bbox_main[2] - bbox_main[0]
    x_main = (qr_w - w_main) // 2
    draw.text((x_main, qr_h + padding), label, fill="black", font=font_main)

    # Gerätename darunter
    bbox_sub = draw.textbbox((0, 0), label_secondary, font=font_sub)
    w_sub = bbox_sub[2] - bbox_sub[0]
    x_sub = (qr_w - w_sub) // 2
    draw.text((x_sub, qr_h + padding + 22), label_secondary, fill="#555555", font=font_sub)

    final_img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# ---------------------------------------------------------------------------
# QR-Scan → Ausleihe triggern
# ---------------------------------------------------------------------------

@geraet_router.post(
    "/{geraet_id}/scan-ausleihe",
    response_model=AusleiheResponse,
    status_code=201,
    summary="QR-Code scannen → Ausleihe starten",
)
def scan_and_ausleihen(
    geraet_id: int,
    db: Session = Depends(get_db),
    current_user: Benutzer = Depends(get_current_user),
) -> AusleiheResponse:
    """Wird aufgerufen, wenn ein Nutzer den QR-Code eines Geräts scannt.

    Erstellt direkt eine Ausleihe – kein weiterer Klick in der UI nötig.
    Das Gerät muss entweder verfügbar sein, oder der Nutzer muss eine
    aktive Reservierung für dieses Gerät besitzen.
    """
    payload = AusleiheCreate(geraet_id=geraet_id)
    return crud_ausleihen.create(db, payload, current_user)


# ---------------------------------------------------------------------------
# NFC-Payload
# ---------------------------------------------------------------------------

@geraet_router.get(
    "/{geraet_id}/nfc-payload",
    response_model=NfcPayloadResponse,
    summary="NFC NDEF-Payload für ein Gerät abrufen",
)
def get_nfc_payload(
    geraet_id: int,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> NfcPayloadResponse:
    geraet = crud.get_by_id(db, geraet_id)
    url = geraet.qr_code_url
    return NfcPayloadResponse(geraet_id=geraet.id, url=url, ndef_uri_record=url)


# ---------------------------------------------------------------------------
# NFC-Resolve
# ---------------------------------------------------------------------------

@nfc_router.post(
    "/resolve",
    response_model=NfcResolveResponse,
    summary="NFC-URL zu Gerätedaten auflösen",
)
def resolve_nfc_url(
    payload: NfcResolveRequest,
    db: Session = Depends(get_db),
    _: Benutzer = Depends(get_current_user),
) -> NfcResolveResponse:
    match = _GERAET_ID_RE.search(payload.url)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL-Format ungültig oder Gerät nicht gefunden.",
        )
    geraet_id = int(match.group(1))
    geraet = crud.get_by_id(db, geraet_id)
    return NfcResolveResponse.model_validate(geraet)
