from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Bildungseinrichtung(Base):
    __tablename__ = 'bildungseinrichtungen'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    strasse = Column(String(255), nullable=True)
    hausnummer = Column(String(20), nullable=True)
    plz = Column(String(10), nullable=True)
    ort = Column(String(255), nullable=True)
    bundesland = Column(String(255), nullable=True)

    # Relationen (als String, um zirkuläre Imports zu vermeiden)
    standorte = relationship("Standort", back_populates="bildungseinrichtung")
