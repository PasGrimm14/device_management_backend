"""feature_updates: neuer_status_langzeit_reservierung

Revision ID: e5f7a9c01b23
Revises: d4e6f8b90c13
Create Date: 2026-04-20 00:00:00.000000

Aenderungen:
- geraete: Spalte `langzeit_ausleihe` (Boolean, default False)
- geraete: Status 'zur Zeit nicht vorhanden' hinzugefuegt
- ausleihen: Spalte `langzeit_verlaengerung_genutzt` (Boolean, default False)

Strategie fuer ENUM-Erweiterung mit Umlauten (MySQL DataError 1265):
  Bestehende Werte mit Umlauten werden ZUERST in reine ASCII-Platzhalter
  umgeschrieben (z.B. 'verfuegbar_tmp', 'ausser_betrieb_tmp').
  Dann: ENUM -> VARCHAR -> neuer ENUM nur mit ASCII-Werten ->
  UPDATE zurueck auf echte Umlaut-Werte -> finaler ENUM mit Umlauten.
  MySQL muss so nie Umlaut-Datenbankwerte gegen Umlaut-SQL-Strings matchen.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'e5f7a9c01b23'
down_revision: Union[str, None] = 'd4e6f8b90c13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Umlaut-Werte als Python unicode escapes (werden zu echten Zeichen kompiliert)
VERFUEGBAR   = 'verf\u00fcgbar'       # verfügbar
AUSSER       = 'au\u00dfer Betrieb'   # außer Betrieb
NICHT_VORH   = 'zur Zeit nicht vorhanden'

# ASCII-Platzhalter
TMP_VERF     = 'verfuegbar_tmp'
TMP_AUSSER   = 'ausser_betrieb_tmp'


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Bestehende Umlaut-Werte -> ASCII-Platzhalter
    #    UPDATE vergleicht Byte-fuer-Byte wie gespeichert -> kein Charset-Problem
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_VERF}'   WHERE status = '{VERFUEGBAR}'"))
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_AUSSER}' WHERE status = '{AUSSER}'"))

    # 2. ENUM -> VARCHAR (kein Wert-Check)
    conn.execute(text(
        "ALTER TABLE geraete MODIFY COLUMN status "
        "VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # 3. VARCHAR -> ENUM nur mit ASCII-Werten (kein Umlaut-Matching noetig)
    conn.execute(text(
        f"ALTER TABLE geraete MODIFY COLUMN status "
        f"ENUM('{TMP_VERF}','ausgeliehen','reserviert','defekt','{TMP_AUSSER}','{NICHT_VORH}') "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # 4. ASCII-Platzhalter -> echte Umlaut-Werte
    conn.execute(text(f"UPDATE geraete SET status = '{VERFUEGBAR}' WHERE status = '{TMP_VERF}'"))
    conn.execute(text(f"UPDATE geraete SET status = '{AUSSER}'     WHERE status = '{TMP_AUSSER}'"))

    # 5. ENUM -> finaler ENUM mit echten Umlauten
    #    Jetzt stimmen DB-Werte und SQL-Strings exakt ueberein (beide utf8mb4)
    conn.execute(text(
        f"ALTER TABLE geraete MODIFY COLUMN status "
        f"ENUM('{VERFUEGBAR}','ausgeliehen','reserviert','defekt','{AUSSER}','{NICHT_VORH}') "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # 6. Neue Boolean-Spalten
    op.add_column('geraete',
        sa.Column('langzeit_ausleihe', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('ausleihen',
        sa.Column('langzeit_verlaengerung_genutzt', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    conn = op.get_bind()

    op.drop_column('ausleihen', 'langzeit_verlaengerung_genutzt')
    op.drop_column('geraete', 'langzeit_ausleihe')

    # Neuen Status auf verfuegbar zuruecksetzen
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_VERF}' WHERE status = '{NICHT_VORH}'"))
    # Umlaute -> Platzhalter
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_VERF}'   WHERE status = '{VERFUEGBAR}'"))
    conn.execute(text(f"UPDATE geraete SET status = '{TMP_AUSSER}' WHERE status = '{AUSSER}'"))

    # ENUM -> VARCHAR
    conn.execute(text(
        "ALTER TABLE geraete MODIFY COLUMN status "
        "VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # VARCHAR -> alter ENUM (nur ASCII-Platzhalter)
    conn.execute(text(
        f"ALTER TABLE geraete MODIFY COLUMN status "
        f"ENUM('{TMP_VERF}','ausgeliehen','reserviert','defekt','{TMP_AUSSER}') "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))

    # Platzhalter -> echte Umlaut-Werte
    conn.execute(text(f"UPDATE geraete SET status = '{VERFUEGBAR}' WHERE status = '{TMP_VERF}'"))
    conn.execute(text(f"UPDATE geraete SET status = '{AUSSER}'     WHERE status = '{TMP_AUSSER}'"))

    # Finaler alter ENUM mit Umlauten
    conn.execute(text(
        f"ALTER TABLE geraete MODIFY COLUMN status "
        f"ENUM('{VERFUEGBAR}','ausgeliehen','reserviert','defekt','{AUSSER}') "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"
    ))
