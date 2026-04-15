"""Statistik-Endpoint für das Gerätemanagementsystem.

Stellt einen Admin-geschützten Endpoint bereit, der aggregierte Kennzahlen
zu Geräten und Ausleihen liefert.
"""
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.ausleihe import Ausleihe
from app.models.base import AusleihStatus, GeraeteStatus
from app.models.benutzer import Benutzer
from app.models.geraet import Geraet

router = APIRouter()


class StatistikResponse(BaseModel):
    """Aggregierte Kennzahlen des Geräteverwaltungssystems."""

    geraete_gesamt: int
    geraete_nach_status: dict[str, int]
    ausleihen_gesamt: int
    ausleihen_aktiv: int
    ausleihen_ueberfaellig: int
    durchschnittliche_ausleihdauer_tage: float
    top_geraete: list[dict[str, Any]]


@router.get("/", response_model=StatistikResponse, summary="Systemstatistiken abrufen")
def get_statistik(
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    """Gibt aggregierte Statistiken zu Geräten und Ausleihen zurück.

    Nur für Administratoren zugänglich.
    """
    # Geräte-Statistiken
    geraete_gesamt: int = db.query(func.count(Geraet.id)).scalar() or 0

    status_counts = (
        db.query(Geraet.status, func.count(Geraet.id))
        .group_by(Geraet.status)
        .all()
    )
    geraete_nach_status = {row[0].value: row[1] for row in status_counts}
    # Fehlende Status-Werte mit 0 auffüllen
    for s in GeraeteStatus:
        geraete_nach_status.setdefault(s.value, 0)

    # Ausleihen-Statistiken
    ausleihen_gesamt: int = db.query(func.count(Ausleihe.id)).scalar() or 0
    ausleihen_aktiv: int = (
        db.query(func.count(Ausleihe.id))
        .filter(Ausleihe.status == AusleihStatus.AKTIV)
        .scalar()
        or 0
    )
    ausleihen_ueberfaellig: int = (
        db.query(func.count(Ausleihe.id))
        .filter(Ausleihe.status == AusleihStatus.UEBERFAELLIG)
        .scalar()
        or 0
    )

    # Durchschnittliche Ausleihdauer (nur abgeschlossene Ausleihen)
    abgeschlossene = (
        db.query(Ausleihe)
        .filter(
            Ausleihe.status == AusleihStatus.ABGESCHLOSSEN,
            Ausleihe.tatsaechliches_rueckgabedatum.isnot(None),
        )
        .all()
    )
    if abgeschlossene:
        gesamttage = sum(
            (a.tatsaechliches_rueckgabedatum - a.startdatum).days
            for a in abgeschlossene
        )
        durchschnittliche_ausleihdauer_tage = round(gesamttage / len(abgeschlossene), 2)
    else:
        durchschnittliche_ausleihdauer_tage = 0.0

    # Top 5 meistausgeliehene Geräte
    top_geraete_rows = (
        db.query(Ausleihe.geraet_id, func.count(Ausleihe.id).label("anzahl"))
        .group_by(Ausleihe.geraet_id)
        .order_by(func.count(Ausleihe.id).desc())
        .limit(5)
        .all()
    )
    top_geraete = []
    for geraet_id, anzahl in top_geraete_rows:
        geraet = db.get(Geraet, geraet_id)
        top_geraete.append({
            "geraet_id": geraet_id,
            "name": geraet.name if geraet else "",
            "anzahl_ausleihen": anzahl,
        })

    return StatistikResponse(
        geraete_gesamt=geraete_gesamt,
        geraete_nach_status=geraete_nach_status,
        ausleihen_gesamt=ausleihen_gesamt,
        ausleihen_aktiv=ausleihen_aktiv,
        ausleihen_ueberfaellig=ausleihen_ueberfaellig,
        durchschnittliche_ausleihdauer_tage=durchschnittliche_ausleihdauer_tage,
        top_geraete=top_geraete,
    )
