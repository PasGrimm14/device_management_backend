"""Export-Endpoints für Ausleihdaten.

Stellt Admin-geschützte Endpoints bereit, um Ausleihdaten als CSV
herunterzuladen.
"""
import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.ausleihe import Ausleihe
from app.models.base import AusleihStatus
from app.models.benutzer import Benutzer

router = APIRouter()


@router.get("/ausleihen", summary="Ausleihdaten als CSV exportieren")
def export_ausleihen(
    status: Optional[AusleihStatus] = Query(default=None, description="Filtert nach Ausleihstatus"),
    von: Optional[date] = Query(default=None, description="Startdatum (inklusiv)"),
    bis: Optional[date] = Query(default=None, description="Enddatum (inklusiv)"),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    """Exportiert alle Ausleihen als CSV-Datei.

    Nur für Administratoren zugänglich. Filterung nach Status und Zeitraum möglich.
    """
    q = db.query(Ausleihe)
    if status is not None:
        q = q.filter(Ausleihe.status == status)
    if von is not None:
        q = q.filter(Ausleihe.startdatum >= von)
    if bis is not None:
        q = q.filter(Ausleihe.startdatum <= bis)

    ausleihen = q.all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        "id",
        "geraet_id",
        "geraet_name",
        "nutzer_id",
        "nutzer_email",
        "startdatum",
        "geplantes_rueckgabedatum",
        "tatsaechliches_rueckgabedatum",
        "status",
        "verlaengerungen_anzahl",
    ])

    for ausleihe in ausleihen:
        geraet_name = ausleihe.geraet.name if ausleihe.geraet else ""
        nutzer_email = ausleihe.nutzer.email if ausleihe.nutzer else ""
        writer.writerow([
            ausleihe.id,
            ausleihe.geraet_id,
            geraet_name,
            ausleihe.nutzer_id,
            nutzer_email,
            ausleihe.startdatum.isoformat() if ausleihe.startdatum else "",
            ausleihe.geplantes_rueckgabedatum.isoformat() if ausleihe.geplantes_rueckgabedatum else "",
            ausleihe.tatsaechliches_rueckgabedatum.isoformat() if ausleihe.tatsaechliches_rueckgabedatum else "",
            ausleihe.status.value if ausleihe.status else "",
            ausleihe.verlaengerungen_anzahl,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ausleihen.csv"},
    )
