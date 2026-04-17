from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.base import AktionType


class AuditLogResponse(BaseModel):
    """Nur lesbar – AuditLogs werden ausschließlich serverseitig erstellt."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    zeitstempel: datetime
    nutzer_id: int
    nutzer_name: Optional[str] = None   # Klarname, wird im Endpoint befüllt
    geraet_id: Optional[int] = None
    aktion: AktionType
    details: Optional[str] = None
