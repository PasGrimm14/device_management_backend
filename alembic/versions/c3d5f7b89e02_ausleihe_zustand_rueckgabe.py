"""Ausleihe: Zustandsbeschreibung bei Rueckgabe

Revision ID: c3d5f7b89e02
Revises: b2c4e6a78d91
Create Date: 2026-04-15 10:05:00.000000

Änderungen:
- ausleihen: Spalte `zustand_bei_rueckgabe` (Text, nullable) hinzugefügt

Ermöglicht die Erfassung von Schäden oder besonderen Zuständen beim
Rückgabe-Vorgang. Wenn ein Zustand eingetragen wird, wechselt das Gerät
automatisch in den Status DEFEKT.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d5f7b89e02'
down_revision: Union[str, None] = 'b2c4e6a78d91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ausleihen',
        sa.Column('zustand_bei_rueckgabe', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('ausleihen', 'zustand_bei_rueckgabe')
