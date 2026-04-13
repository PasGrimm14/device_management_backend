from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, ReservierungsStatus

class Reservierung(Base):
    __tablename__ = 'reservierungen'

    id = Column(Integer, primary_key=True, autoincrement=True)
    geraet_id = Column(Integer, ForeignKey('geraete.id'), nullable=False)
    nutzer_id = Column(Integer, ForeignKey('benutzer.id'), nullable=False)
    
    erstellt_am = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reserviert_fuer_datum = Column(Date, nullable=False)
    status = Column(Enum(ReservierungsStatus), default=ReservierungsStatus.AKTIV, nullable=False)

    # Relationen
    geraet = relationship("Geraet", back_populates="reservierungen")
    nutzer = relationship("Benutzer", back_populates="reservierungen")