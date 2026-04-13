from sqlalchemy import Column, Integer, String, Date, Text, Enum
from sqlalchemy.orm import relationship
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
    standort = Column(String(100))
    status = Column(Enum(GeraeteStatus), default=GeraeteStatus.VERFUEGBAR, nullable=False)
    anschaffungsdatum = Column(Date)
    bemerkungen = Column(Text)

    # Relationen
    ausleihen = relationship("Ausleihe", back_populates="geraet")
    reservierungen = relationship("Reservierung", back_populates="geraet")
    audit_logs = relationship("AuditLog", back_populates="geraet")

    @property
    def qr_code_url(self):
        """Generiert die eindeutige URL für den QR-Code."""
        return f"https://svschefflenz.online/geraete/{self.id}"