from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.benutzer import Benutzer


def _enrich(logs: list[AuditLog], db: Session) -> list[dict]:
    """Reichert AuditLog-Objekte um den Klarnamen des Benutzers an."""
    # Alle benötigten Benutzer-IDs einmalig laden (kein N+1)
    nutzer_ids = {log.nutzer_id for log in logs}
    nutzer_map: dict[int, str] = {}
    if nutzer_ids:
        rows = db.query(Benutzer.id, Benutzer.name).filter(Benutzer.id.in_(nutzer_ids)).all()
        nutzer_map = {row.id: row.name for row in rows}

    result = []
    for log in logs:
        d = {
            "id": log.id,
            "zeitstempel": log.zeitstempel,
            "nutzer_id": log.nutzer_id,
            "nutzer_name": nutzer_map.get(log.nutzer_id, f"Benutzer #{log.nutzer_id}"),
            "geraet_id": log.geraet_id,
            "aktion": log.aktion,
            "details": log.details,
        }
        result.append(d)
    return result


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[dict]:
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.zeitstempel.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return _enrich(logs, db)


def get_by_geraet(db: Session, geraet_id: int, skip: int = 0, limit: int = 100) -> list[dict]:
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.geraet_id == geraet_id)
        .order_by(AuditLog.zeitstempel.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return _enrich(logs, db)
