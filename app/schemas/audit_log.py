from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.base import AktionType


class AuditLogResponse(BaseModel):
    """Nur lesbar – AuditLogs werden ausschließlich serverseitig erstellt."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    zeitstempel: datetime
    nutzer_id: int
    geraet_id: Optional[int] = None
    aktion: AktionType
    details: Optional[str] = None
