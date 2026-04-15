"""Ausleihe: E-Mail-Flags fuer Erinnerung und Mahnung

Revision ID: b2c4e6a78d91
Revises: a3f5c8d12e47
Create Date: 2026-04-15 10:00:00.000000

Änderungen:
- ausleihen: Spalte `erinnerung_gesendet` (Boolean, default False) hinzugefügt
- ausleihen: Spalte `mahnung_gesendet` (Boolean, default False) hinzugefügt

Beide Flags werden vom Scheduler gesetzt, um doppelten E-Mail-Versand zu
verhindern.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c4e6a78d91'
down_revision: Union[str, None] = 'a3f5c8d12e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ausleihen',
        sa.Column('erinnerung_gesendet', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'ausleihen',
        sa.Column('mahnung_gesendet', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('ausleihen', 'mahnung_gesendet')
    op.drop_column('ausleihen', 'erinnerung_gesendet')
