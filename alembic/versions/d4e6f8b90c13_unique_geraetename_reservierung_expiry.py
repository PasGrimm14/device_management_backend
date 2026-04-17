"""unique_geraetename_reservierung_expiry

Revision ID: d4e6f8b90c13
Revises: c3d5f7b89e02
Create Date: 2026-04-17 00:00:00.000000

Änderungen:
- geraete: Spalte `unique_name` (String, nullable, unique) hinzugefügt
  Format: {Kategorie}-{Hersteller}-{Nummer} z.B. Laptop-Apple-1000
- reservierungen: Spalte `ablaufdatum` (DateTime, nullable) hinzugefügt
  Wird beim Anlegen auf erstellt_am + 3 Tage gesetzt
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e6f8b90c13'
down_revision: Union[str, None] = 'c3d5f7b89e02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'geraete',
        sa.Column('unique_name', sa.String(length=150), nullable=True),
    )
    op.create_index('ix_geraete_unique_name', 'geraete', ['unique_name'], unique=True)

    op.add_column(
        'reservierungen',
        sa.Column('ablaufdatum', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('reservierungen', 'ablaufdatum')
    op.drop_index('ix_geraete_unique_name', table_name='geraete')
    op.drop_column('geraete', 'unique_name')
