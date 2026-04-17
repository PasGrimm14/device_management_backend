import re
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.base import AktionType, GeraeteStatus
from app.models.geraet import Geraet
from app.schemas.geraet import GeraetCreate, GeraetUpdate

# Unique-Name beginnt bei dieser Basis-Nummer
_UNIQUE_NAME_START = 1000
_UNIQUE_NAME_STEP = 5   # Schrittweite, damit Lücken möglich sind (1000,1005,1010,…)


def _slugify(text: str) -> str:
    """Konvertiert beliebigen Text in einen URL-/Label-freundlichen Slug."""
    if not text:
        return "Unbekannt"
    # Unicode → ASCII-ähnlich, Leerzeichen → Bindestrich, Sonderzeichen entfernen
    text = text.strip()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text, flags=re.UNICODE)
    return text or "Unbekannt"


def _generate_unique_name(db: Session, kategorie: Optional[str], hersteller: Optional[str]) -> str:
    """Generiert einen eindeutigen Gerätenamen im Format Kategorie-Hersteller-NNNN."""
    kat = _slugify(kategorie or "Sonstiges")
    her = _slugify(hersteller or "Unbekannt")
    prefix = f"{kat}-{her}-"

    # Alle vorhandenen unique_names mit diesem Prefix laden und höchste Nummer ermitteln
    existing = (
        db.query(Geraet.unique_name)
        .filter(Geraet.unique_name.like(f"{prefix}%"))
        .all()
    )
    max_nr = _UNIQUE_NAME_START - _UNIQUE_NAME_STEP
    for (uname,) in existing:
        if uname:
            parts = uname.rsplit("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                max_nr = max(max_nr, int(parts[1]))

    next_nr = max_nr + _UNIQUE_NAME_STEP
    return f"{prefix}{next_nr}"


def get_all(
    db: Session,
    *,
    filter_status: Optional[GeraeteStatus] = None,
    filter_kategorie: Optional[str] = None,
    filter_search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Geraet]:
    q = db.query(Geraet)
    if filter_status is not None:
        q = q.filter(Geraet.status == filter_status)
    if filter_kategorie is not None:
        q = q.filter(Geraet.kategorie == filter_kategorie)
    if filter_search is not None:
        term = f"%{filter_search}%"
        q = q.filter(
            Geraet.name.ilike(term)
            | Geraet.hersteller.ilike(term)
            | Geraet.modell.ilike(term)
            | Geraet.inventar_nummer.ilike(term)
            | Geraet.unique_name.ilike(term)
        )
    return q.offset(skip).limit(limit).all()


def get_by_id(db: Session, geraet_id: int) -> Geraet:
    geraet = db.get(Geraet, geraet_id)
    if geraet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gerät nicht gefunden.")
    return geraet


def create(db: Session, payload: GeraetCreate, nutzer_id: int) -> Geraet:
    if db.query(Geraet).filter(Geraet.inventar_nummer == payload.inventar_nummer).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inventarnummer '{payload.inventar_nummer}' ist bereits vergeben.",
        )

    unique_name = _generate_unique_name(db, payload.kategorie, payload.hersteller)

    geraet = Geraet(**payload.model_dump(), unique_name=unique_name)
    db.add(geraet)
    db.flush()
    db.add(AuditLog(
        nutzer_id=nutzer_id,
        geraet_id=geraet.id,
        aktion=AktionType.ANGELEGT,
        details=f"Gerät '{geraet.name}' (unique_name: {unique_name}) angelegt.",
    ))
    db.commit()
    db.refresh(geraet)
    return geraet


def update(db: Session, geraet_id: int, payload: GeraetUpdate, nutzer_id: int) -> Geraet:
    geraet = get_by_id(db, geraet_id)
    changes = payload.model_dump(exclude_unset=True)
    old_status = geraet.status

    for field, value in changes.items():
        setattr(geraet, field, value)

    aktion = AktionType.STATUS_AENDERUNG if "status" in changes else AktionType.BEARBEITET
    details = f"Status: {old_status} → {geraet.status}" if "status" in changes else str(changes)
    db.add(AuditLog(nutzer_id=nutzer_id, geraet_id=geraet.id, aktion=aktion, details=details))
    db.commit()
    db.refresh(geraet)
    return geraet


def delete(db: Session, geraet_id: int) -> None:
    geraet = get_by_id(db, geraet_id)
    db.delete(geraet)
    db.commit()
