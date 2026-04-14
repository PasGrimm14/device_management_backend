"""GER-51 standort db struktur

Revision ID: a3f5c8d12e47
Revises: c7e9f1a234b5
Create Date: 2026-04-15 00:00:00.000000

Änderungen:
- Neue Tabelle: bildungseinrichtungen
- Neue Tabelle: standorte (FK → bildungseinrichtungen)
- Neue Tabelle: boxen (FK → standorte)
- geraete: Spalte `standort` (String) entfernt
- geraete: Spalte `box_id` (FK → boxen) hinzugefügt

MySQL-Hinweise:
- Tabellen werden in FK-Reihenfolge angelegt (bildungseinrichtungen → standorte → boxen)
- DROP COLUMN und ADD COLUMN in geraete als separate ALTER TABLE Statements
- Kein batch-mode (wird nur für SQLite benötigt)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f5c8d12e47'
down_revision: Union[str, None] = 'c7e9f1a234b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. bildungseinrichtungen (keine FK-Abhängigkeiten)
    op.create_table(
        'bildungseinrichtungen',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('strasse', sa.String(length=255), nullable=True),
        sa.Column('hausnummer', sa.String(length=20), nullable=True),
        sa.Column('plz', sa.String(length=10), nullable=True),
        sa.Column('ort', sa.String(length=255), nullable=True),
        sa.Column('bundesland', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. standorte (FK → bildungseinrichtungen)
    op.create_table(
        'standorte',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('bildungseinrichtung_id', sa.Integer(), nullable=False),
        sa.Column('gebaeude', sa.String(length=255), nullable=True),
        sa.Column('raum', sa.String(length=100), nullable=True),
        sa.Column('beschreibung', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['bildungseinrichtung_id'], ['bildungseinrichtungen.id'],
                                name='fk_standorte_bildungseinrichtung_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 3. boxen (FK → standorte)
    op.create_table(
        'boxen',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('box_nummer', sa.String(length=50), nullable=True),
        sa.Column('standort_id', sa.Integer(), nullable=False),
        sa.Column('beschreibung', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['standort_id'], ['standorte.id'],
                                name='fk_boxen_standort_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 4a. Altes standort-Feld aus geraete entfernen
    op.drop_column('geraete', 'standort')

    # 4b. Neue box_id-Spalte in geraete hinzufügen (separates ALTER TABLE)
    op.add_column(
        'geraete',
        sa.Column('box_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_geraete_box_id',
        'geraete', 'boxen',
        ['box_id'], ['id'],
    )


def downgrade() -> None:
    # Umgekehrte Reihenfolge: zuerst abhängige Constraints/Spalten entfernen
    op.drop_constraint('fk_geraete_box_id', 'geraete', type_='foreignkey')
    op.drop_column('geraete', 'box_id')

    # standort-Spalte wiederherstellen
    op.add_column(
        'geraete',
        sa.Column('standort', sa.String(length=100), nullable=True),
    )

    # Tabellen in umgekehrter FK-Reihenfolge löschen
    op.drop_table('boxen')
    op.drop_table('standorte')
    op.drop_table('bildungseinrichtungen')
