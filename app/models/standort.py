from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Standort(Base):
    __tablename__ = 'standorte'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bildungseinrichtung_id = Column(Integer, ForeignKey('bildungseinrichtungen.id'), nullable=False)
    gebaeude = Column(String(255), nullable=True)
    raum = Column(String(100), nullable=True)
    beschreibung = Column(Text, nullable=True)

    # Relationen (als String, um zirkuläre Imports zu vermeiden)
    bildungseinrichtung = relationship("Bildungseinrichtung", back_populates="standorte")
    boxen = relationship("Box", back_populates="standort")
