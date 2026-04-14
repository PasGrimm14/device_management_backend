from sqlalchemy import Column, ForeignKey, Integer, String, Date, Text, Enum
from sqlalchemy.orm import relationship

from app.core.config import settings
from .base import Base, GeraeteStatus

class Geraet(Base):
    __tablename__ = 'geraete'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inventar_nummer = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    kategorie = Column(String(50), index=True)
    hersteller = Column(String(50))
    modell = Column(String(50))
    seriennummer = Column(String(100), unique=True)
    status = Column(Enum(GeraeteStatus), default=GeraeteStatus.VERFUEGBAR, nullable=False)
    anschaffungsdatum = Column(Date)
    bemerkungen = Column(Text)
    bild_id = Column(Integer, ForeignKey("geraet_bilder.id"), nullable=True)
    box_id = Column(Integer, ForeignKey("boxen.id"), nullable=True)

    # Relationen
    bild = relationship("GeraetBild", back_populates="geraete")
    box = relationship("Box", back_populates="geraete")
    ausleihen = relationship("Ausleihe", back_populates="geraet")
    reservierungen = relationship("Reservierung", back_populates="geraet")
    audit_logs = relationship("AuditLog", back_populates="geraet")

    @property
    def qr_code_url(self):
        """Generiert die eindeutige URL für den QR-Code."""
        return f"{settings.BASE_URL}/geraete/{self.id}"