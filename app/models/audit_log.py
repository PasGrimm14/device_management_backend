from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, AktionType

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    zeitstempel = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    nutzer_id = Column(Integer, ForeignKey('benutzer.id'), nullable=False)
    geraet_id = Column(Integer, ForeignKey('geraete.id'), nullable=True)
    aktion = Column(Enum(AktionType), nullable=False)
    details = Column(Text, nullable=True)

    # Relationen
    nutzer = relationship("Benutzer", back_populates="audit_logs")
    geraet = relationship("Geraet", back_populates="audit_logs")