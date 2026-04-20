"""feature_updates: neuer_status_langzeit_reservierung

Revision ID: e5f7a9c01b23
Revises: d4e6f8b90c13
Create Date: 2026-04-20 00:00:00.000000

Änderungen:
- geraete: Spalte `langzeit_ausleihe` (Boolean, default False)
- geraete: Status 'zur Zeit nicht vorhanden' hinzugefügt
- ausleihen: Spalte `langzeit_verlaengerung_genutzt` (Boolean, default False)

Strategie für ENUM-Erweiterung mit Umlauten (MySQL DataError 1265):
  MySQL kann bestehende Umlaut-Werte beim MODIFY COLUMN nicht zuordnen,
  wenn der interne Charset der Verbindung nicht passt.
  Lösung: Spalte temporär auf VARCHAR(50) ändern (keine Wert-Validierung),
  dann auf den neuen ENUM zurücksetzen. Bestehende Werte bleiben dabei
  exakt erhalten, da VARCHAR alle Strings akzeptiert.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'e5f7a9c01b23'
down_revision: Union[str, None] = 'd4e6f8b90c13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Schritt 1: status → VARCHAR(50)
    # VARCHAR hat keine Wert-Einschränkung → bestehende Umlaut-Werte bleiben erhalten
    conn.execute(text(
        "ALTER TABLE geraete "
        "MODIFY COLUMN status VARCHAR(50) "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Schritt 2: VARCHAR → erweiterter ENUM (jetzt ohne Konflikt, da Werte bereits korrekt gespeichert)
    conn.execute(text(
        "ALTER TABLE geraete "
        "MODIFY COLUMN status "
        "ENUM("
            "'verf\u00fcgbar',"        # verfügbar
            "'ausgeliehen',"
            "'reserviert',"
            "'defekt',"
            "'au\u00dfer Betrieb',"    # außer Betrieb
            "'zur Zeit nicht vorhanden'"
        ") "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Langzeit-Flag für Geräte
    op.add_column(
        'geraete',
        sa.Column(
            'langzeit_ausleihe',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Langzeit-Verlängerung-Flag für Ausleihen
    op.add_column(
        'ausleihen',
        sa.Column(
            'langzeit_verlaengerung_genutzt',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    conn = op.get_bind()

    op.drop_column('ausleihen', 'langzeit_verlaengerung_genutzt')
    op.drop_column('geraete', 'langzeit_ausleihe')

    # Schritt 1: status → VARCHAR (damit der neue Wert keine Fehler wirft)
    conn.execute(text(
        "ALTER TABLE geraete "
        "MODIFY COLUMN status VARCHAR(50) "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Schritt 2: alten ENUM ohne 'zur Zeit nicht vorhanden' wiederherstellen
    # Achtung: Zeilen mit diesem Wert würden abgeschnitten – daher zuerst bereinigen
    conn.execute(text(
        "UPDATE geraete SET status = 'verf\u00fcgbar' "
        "WHERE status = 'zur Zeit nicht vorhanden'"
    ))

    conn.execute(text(
        "ALTER TABLE geraete "
        "MODIFY COLUMN status "
        "ENUM("
            "'verf\u00fcgbar',"
            "'ausgeliehen',"
            "'reserviert',"
            "'defekt',"
            "'au\u00dfer Betrieb'"
        ") "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))
