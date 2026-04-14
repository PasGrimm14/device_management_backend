"""geraet_bilder_tabelle_und_bild_fk

Revision ID: c7e9f1a234b5
Revises: b1f0738f6559
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7e9f1a234b5'
down_revision: Union[str, None] = 'b1f0738f6559'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Neue Tabelle für Gerätebilder ###
    op.create_table(
        'geraet_bilder',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dateiname', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=50), nullable=False),
        sa.Column('hochgeladen_am', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dateiname'),
    )

    # ### FK-Spalte bild_id in geraete ###
    op.add_column(
        'geraete',
        sa.Column('bild_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_geraete_bild_id',
        'geraete', 'geraet_bilder',
        ['bild_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_geraete_bild_id', 'geraete', type_='foreignkey')
    op.drop_column('geraete', 'bild_id')
    op.drop_table('geraet_bilder')
