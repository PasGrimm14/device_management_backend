"""feature_updates: neuer_status_langzeit_reservierung

Revision ID: e5f7a9c01b23
Revises: d4e6f8b90c13
Create Date: 2026-04-20 00:00:00.000000

Aenderungen:
- geraete: Spalte langzeit_ausleihe (Boolean, default False)
- geraete: Status 'zur Zeit nicht vorhanden' hinzugefuegt
- ausleihen: Spalte langzeit_verlaengerung_genutzt (Boolean, default False)

Strategie fuer ENUM-Erweiterung mit Umlauten (MySQL DataError 1265):

Das Problem: MySQL vergleicht beim ALTER TABLE...ENUM die gespeicherten
Bytes gegen den SQL-String. Wenn die Spalte in latin1 gespeichert ist
(fc fuer ue, df fuer ss), aber der Python-String utf8mb4 sendet (c3bc, c39f),
schlaegt der Vergleich fehl -- auch nach SET NAMES oder VARCHAR-Zwischenschritt.

Loesung: MySQL UNHEX() und HEX() verwenden.
- UNHEX('76657266fc67626172') = 'verfuegbar' in latin1-Bytes
  Das funktioniert charset-unabhaengig, weil UNHEX() reine Bytes produziert.
- UPDATE mit UNHEX matcht exakt die gespeicherten Bytes -- garantiert.
- Danach: VARCHAR mit utf8mb4 -> neuer ENUM mit utf8mb4.

Hex-Werte:
  'verfuegbar'   latin1: 76657266fc67626172
                 utf8mb4: 76657266c3bc67626172
  'ausser Betrieb' latin1: 6175df65722042657472696562
                   utf8mb4: 6175c39f65722042657472696562
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'e5f7a9c01b23'
down_revision: Union[str, None] = 'd4e6f8b90c13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TMP_VERF   = 'verfuegbar_tmp'
TMP_AUSSER = 'ausser_betrieb_tmp'
NICHT_VORH = 'zur Zeit nicht vorhanden'

# Hex der latin1-kodierten Werte (wie MySQL sie intern speichert)
HEX_VERF_LATIN1   = '76657266fc67626172'          # verfügbar in latin1
HEX_AUSSER_LATIN1 = '6175df65722042657472696562'  # außer Betrieb in latin1

# Hex der utf8mb4-kodierten Werte
HEX_VERF_UTF8   = '76657266c3bc67626172'
HEX_AUSSER_UTF8 = '6175c39f65722042657472696562'


def upgrade() -> None:
    conn = op.get_bind()

    # Schritt 1: Herausfinden ob die Spalte latin1 oder utf8mb4 speichert
    # Wir versuchen zuerst mit latin1-Hex, dann mit utf8mb4-Hex
    # UPDATE mit UNHEX() matcht die Bytes direkt -- charset-agnostisch

    # latin1-Variante versuchen
    conn.execute(text(
        f"UPDATE geraete SET status = '{TMP_VERF}' "
        f"WHERE HEX(status) = '{HEX_VERF_LATIN1.upper()}'"
    ))
    conn.execute(text(
        f"UPDATE geraete SET status = '{TMP_AUSSER}' "
        f"WHERE HEX(status) = '{HEX_AUSSER_LATIN1.upper()}'"
    ))

    # utf8mb4-Variante versuchen (falls latin1 nicht gematcht hat)
    conn.execute(text(
        f"UPDATE geraete SET status = '{TMP_VERF}' "
        f"WHERE HEX(status) = '{HEX_VERF_UTF8.upper()}'"
    ))
    conn.execute(text(
        f"UPDATE geraete SET status = '{TMP_AUSSER}' "
        f"WHERE HEX(status) = '{HEX_AUSSER_UTF8.upper()}'"
    ))

    # Schritt 2: ENUM -> VARCHAR (kein Wert-Check, alle Platzhalter bleiben)
    conn.execute(text(
        "ALTER TABLE geraete MODIFY COLUMN status "
        "VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Schritt 3: VARCHAR -> ENUM nur mit ASCII-Werten (kein Umlaut-Matching)
    conn.execute(text(
        f"ALTER TABLE geraete MODIFY COLUMN status "
        f"ENUM('{TMP_VERF}','ausgeliehen','reserviert','defekt','{TMP_AUSSER}','{NICHT_VORH}') "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Schritt 4: Platzhalter -> echte Umlaut-Werte (jetzt utf8mb4, normaler String-Match)
    conn.execute(text(f"UPDATE geraete SET status = 'verf\u00fcgbar'    WHERE status = '{TMP_VERF}'"))
    conn.execute(text(f"UPDATE geraete SET status = 'au\u00dfer Betrieb' WHERE status = '{TMP_AUSSER}'"))

    # Schritt 5: ENUM -> finaler ENUM mit echten Umlauten (utf8mb4 <-> utf8mb4: kein Konflikt)
    conn.execute(text(
        "ALTER TABLE geraete MODIFY COLUMN status "
        "ENUM('verf\u00fcgbar','ausgeliehen','reserviert','defekt','au\u00dfer Betrieb','zur Zeit nicht vorhanden') "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Schritt 6: neue Boolean-Spalten
    op.add_column('geraete',
        sa.Column('langzeit_ausleihe', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('ausleihen',
        sa.Column('langzeit_verlaengerung_genutzt', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    conn = op.get_bind()

    op.drop_column('ausleihen', 'langzeit_verlaengerung_genutzt')
    op.drop_column('geraete', 'langzeit_ausleihe')

    # Neuen Status -> verfuegbar_tmp
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_VERF}' WHERE status = 'zur Zeit nicht vorhanden'"))
    # Umlaute -> Platzhalter (utf8mb4 in DB nach upgrade, normaler Match)
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_VERF}'   WHERE status = 'verf\u00fcgbar'"))
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_AUSSER}' WHERE status = 'au\u00dfer Betrieb'"))

    # ENUM -> VARCHAR
    conn.execute(text(
        "ALTER TABLE geraete MODIFY COLUMN status "
        "VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # VARCHAR -> alter ENUM ohne neuen Status (nur ASCII-Platzhalter)
    conn.execute(text(
        f"ALTER TABLE geraete MODIFY COLUMN status "
        f"ENUM('{TMP_VERF}','ausgeliehen','reserviert','defekt','{TMP_AUSSER}') "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Platzhalter -> echte Werte
    conn.execute(text(f"UPDATE geraete SET status = 'verf\u00fcgbar'    WHERE status = '{TMP_VERF}'"))
    conn.execute(text(f"UPDATE geraete SET status = 'au\u00dfer Betrieb' WHERE status = '{TMP_AUSSER}'"))

    # Finaler alter ENUM
    conn.execute(text(
        "ALTER TABLE geraete MODIFY COLUMN status "
        "ENUM('verf\u00fcgbar','ausgeliehen','reserviert','defekt','au\u00dfer Betrieb') "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))
