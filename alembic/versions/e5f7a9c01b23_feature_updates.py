"""feature_updates: neuer_status_langzeit_reservierung

Revision ID: e5f7a9c01b23
Revises: d4e6f8b90c13
Create Date: 2026-04-20 00:00:00.000000

Änderungen:
- geraete: Spalte `langzeit_ausleihe` (Boolean, default False) hinzugefügt
- geraete: Enum GeraeteStatus um 'zur Zeit nicht vorhanden' erweitert
- ausleihen: Spalte `langzeit_verlaengerung_genutzt` (Boolean, default False) hinzugefügt

Fix: ENUM-Erweiterung über zweistufiges ALTER TABLE mit explizitem
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, um DataError 1265
bei vorhandenen Zeilen mit Umlauten zu vermeiden.
Unicode-Escapes (\u00fc = ü, \u00df = ß) umgehen Encoding-Probleme
beim Ausführen des SQL-Strings durch Alembic/PyMySQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'e5f7a9c01b23'
down_revision: Union[str, None] = 'd4e6f8b90c13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ENUM-Werte als Python-Strings (Unicode-Escapes statt direkte Umlaute)
# verf\u00fcgbar  = verfügbar
# au\u00dfer      = außer
_ENUM_ALT = (
    "ENUM("
    "'verf\u00fcgbar',"
    "'ausgeliehen',"
    "'reserviert',"
    "'defekt',"
    "'au\u00dfer Betrieb',"
    "'zur Zeit nicht vorhanden'"
    ") CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)

_ENUM_OLD = (
    "ENUM("
    "'verf\u00fcgbar',"
    "'ausgeliehen',"
    "'reserviert',"
    "'defekt',"
    "'au\u00dfer Betrieb'"
    ") CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)


def upgrade() -> None:
    conn = op.get_bind()

    # Sicherstellen dass die Verbindung UTF-8 verwendet
    conn.execute(text("SET NAMES utf8mb4"))
    conn.execute(text("SET CHARACTER SET utf8mb4"))
    conn.execute(text("SET character_set_connection=utf8mb4"))

    # GeraeteStatus ENUM erweitern – zweistufig:
    # Schritt 1: NULL erlauben → MySQL validiert bestehende Werte nicht streng
    conn.execute(text(f"ALTER TABLE geraete MODIFY COLUMN status {_ENUM_ALT} NULL"))
    # Schritt 2: Zurück auf NOT NULL
    conn.execute(text(f"ALTER TABLE geraete MODIFY COLUMN status {_ENUM_ALT} NOT NULL"))

    # Langzeit-Flag für Geräte
    op.add_column(
        'geraete',
        sa.Column('langzeit_ausleihe', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Langzeit-Verlängerung-Flag für Ausleihen
    op.add_column(
        'ausleihen',
        sa.Column('langzeit_verlaengerung_genutzt', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("SET NAMES utf8mb4"))

    op.drop_column('ausleihen', 'langzeit_verlaengerung_genutzt')
    op.drop_column('geraete', 'langzeit_ausleihe')

    conn.execute(text(f"ALTER TABLE geraete MODIFY COLUMN status {_ENUM_OLD} NOT NULL"))
