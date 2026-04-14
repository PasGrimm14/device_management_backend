from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from .base import Base, BenutzerRolle

# GER-46: Kein separates AuthSession-Modell erforderlich.
#
# Die Authentifizierung basiert auf stateless JWTs (PyJWT). Tokens werden in
# app/core/security.py signiert und ausschließlich über Signatur + Ablaufzeit
# validiert – ohne Datenbankabfrage. Es gibt weder Refresh-Tokens noch eine
# serverseitige Widerrufsliste (Revocation List).
#
# Ein AuthSession-Modell wäre toter Code, solange keiner der Auth-Endpunkte
# Sessions schreibt oder liest. Sollte in Zukunft eine der folgenden
# Anforderungen hinzukommen, muss das Modell nachgezogen werden:
#   - Refresh-Token-Rotation
#   - Token-Widerruf vor Ablauf (z. B. bei Logout oder Passwortänderung)
#   - Mehrfach-Session-Verwaltung pro Benutzer
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