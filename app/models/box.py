from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Box(Base):
    __tablename__ = 'boxen'

    id = Column(Integer, primary_key=True, autoincrement=True)
    box_nummer = Column(String(50), nullable=True)
    standort_id = Column(Integer, ForeignKey('standorte.id'), nullable=False)
    beschreibung = Column(Text, nullable=True)

    # Relationen (als String, um zirkuläre Imports zu vermeiden)
    standort = relationship("Standort", back_populates="boxen")
    geraete = relationship("Geraet", back_populates="box")
