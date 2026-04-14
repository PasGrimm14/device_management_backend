from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GeraetBild(Base):
    __tablename__ = "geraet_bilder"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dateiname = Column(String(255), nullable=False, unique=True)
    mime_type = Column(String(50), nullable=False)
    hochgeladen_am = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Mehrere Geräte können auf dasselbe Bild zeigen
    geraete = relationship("Geraet", back_populates="bild")
