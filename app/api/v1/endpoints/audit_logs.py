from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.crud import audit_logs as crud
from app.models.benutzer import Benutzer
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    return crud.get_all(db, skip=skip, limit=limit)


@router.get("/geraet/{geraet_id}", response_model=list[AuditLogResponse])
def list_audit_logs_fuer_geraet(
    geraet_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Benutzer = Depends(require_admin),
):
    return crud.get_by_geraet(db, geraet_id, skip=skip, limit=limit)
