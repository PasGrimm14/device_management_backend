from datetime import datetime, timedelta, timezone
from sqlalchemy import Boolean, Column, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base, AusleihStatus

class Ausleihe(Base):
    __tablename__ = 'ausleihen'

    id = Column(Integer, primary_key=True, autoincrement=True)
    geraet_id = Column(Integer, ForeignKey('geraete.id'), nullable=False)
    nutzer_id = Column(Integer, ForeignKey('benutzer.id'), nullable=False)

    startdatum = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    geplantes_rueckgabedatum = Column(DateTime, nullable=False)
    tatsaechliches_rueckgabedatum = Column(DateTime, nullable=True)

    status = Column(Enum(AusleihStatus), default=AusleihStatus.AKTIV, nullable=False)
    verlaengerungen_anzahl = Column(Integer, default=0, nullable=False)

    # E-Mail-Flags für Scheduler-Jobs
    erinnerung_gesendet = Column(Boolean, default=False, nullable=False)
    mahnung_gesendet = Column(Boolean, default=False, nullable=False)

    # Zustandsbeschreibung bei Rückgabe (optional)
    zustand_bei_rueckgabe = Column(Text, nullable=True)

    # Relationen
    geraet = relationship("Geraet", back_populates="ausleihen")
    nutzer = relationship("Benutzer", back_populates="ausleihen")

    def init_rueckgabedatum(self):
        if not self.geplantes_rueckgabedatum:
            self.geplantes_rueckgabedatum = self.startdatum + timedelta(days=14)