from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .order_by(AuditLog.zeitstempel.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_geraet(db: Session, geraet_id: int, skip: int = 0, limit: int = 100) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.geraet_id == geraet_id)
        .order_by(AuditLog.zeitstempel.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
