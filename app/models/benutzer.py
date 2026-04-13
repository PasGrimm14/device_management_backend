from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from .base import Base, BenutzerRolle

class Benutzer(Base):
    __tablename__ = 'benutzer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    shibboleth_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    rolle = Column(Enum(BenutzerRolle), default=BenutzerRolle.STANDARD, nullable=False)

    # Relationen (als String, um zirkuläre Imports zu vermeiden)
    ausleihen = relationship("Ausleihe", back_populates="nutzer")
    reservierungen = relationship("Reservierung", back_populates="nutzer")
    audit_logs = relationship("AuditLog", back_populates="nutzer")