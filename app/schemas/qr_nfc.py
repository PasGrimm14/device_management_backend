from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.base import GeraeteStatus


class NfcPayloadResponse(BaseModel):
    """Antwort für den NFC-Payload-Endpoint eines Geräts.

    Enthält alle Daten, die zum Beschreiben eines NFC-Tags benötigt werden.
    `ndef_uri_record` entspricht dem URI-String, der in einen NDEF URI Record
    eingebettet wird (RFC 3986, Typ 0x03 = keine Abkürzung / volle URI).
    """

    geraet_id: int
    url: str
    ndef_uri_record: str


class NfcResolveRequest(BaseModel):
    """Body für POST /nfc/resolve.

    Wird gesendet, wenn ein NFC-Tag ausgelesen wurde und das Frontend
    die hinter der URL stehenden Gerätedaten abrufen möchte.
    """

    url: str


class NfcResolveResponse(BaseModel):
    """Gerätegrunddaten, zurückgegeben nach erfolgreicher NFC-URL-Auflösung."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    seriennummer: str | None
    status: GeraeteStatus
