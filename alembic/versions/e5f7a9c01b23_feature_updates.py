"""feature_updates: neuer_status_langzeit_reservierung

Revision ID: e5f7a9c01b23
Revises: d4e6f8b90c13
Create Date: 2026-04-20 00:00:00.000000

Änderungen:
- geraete: Spalte `langzeit_ausleihe` (Boolean, default False) hinzugefügt
- geraete: Enum GeraeteStatus um 'zur Zeit nicht vorhanden' erweitert
- ausleihen: Spalte `langzeit_verlaengerung_genutzt` (Boolean, default False) hinzugefügt

MySQL-Hinweis: ENUM-Erweiterungen erfordern ALTER TABLE MODIFY COLUMN.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f7a9c01b23'
down_revision: Union[str, None] = 'd4e6f8b90c13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. GeraeteStatus ENUM um neuen Wert erweitern (MySQL: MODIFY COLUMN)
    op.execute(
        "ALTER TABLE geraete MODIFY COLUMN status ENUM("
        "'verfügbar','ausgeliehen','reserviert','defekt','außer Betrieb','zur Zeit nicht vorhanden'"
        ") NOT NULL"
    )

    # 2. Langzeit-Flag für Geräte
    op.add_column(
        'geraete',
        sa.Column('langzeit_ausleihe', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # 3. Langzeit-Verlängerung-Flag für Ausleihen
    op.add_column(
        'ausleihen',
        sa.Column('langzeit_verlaengerung_genutzt', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('ausleihen', 'langzeit_verlaengerung_genutzt')
    op.drop_column('geraete', 'langzeit_ausleihe')

    # Alten ENUM ohne den neuen Wert wiederherstellen
    op.execute(
        "ALTER TABLE geraete MODIFY COLUMN status ENUM("
        "'verfügbar','ausgeliehen','reserviert','defekt','außer Betrieb'"
        ") NOT NULL"
    )