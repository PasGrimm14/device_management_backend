from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.benutzer import Benutzer
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> list[AuditLog]:
    """Gibt alle Audit-Logs zurück (neueste zuerst). Nur für Administratoren."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.zeitstempel.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/geraet/{geraet_id}", response_model=list[AuditLogResponse])
def list_audit_logs_fuer_geraet(
    geraet_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
) -> list[AuditLog]:
    """Gibt alle Audit-Logs für ein bestimmtes Gerät zurück. Nur für Administratoren."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.geraet_id == geraet_id)
        .order_by(AuditLog.zeitstempel.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
