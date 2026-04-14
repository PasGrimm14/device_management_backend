# Device Management Backend

REST-API für ein Geräteverwaltungssystem — entwickelt mit **FastAPI**, **SQLAlchemy** und **MySQL**. Die Anwendung ermöglicht das Verwalten von Geräten, Ausleihen, Reservierungen und Benutzern, inklusive QR-Code-Generierung und Audit-Logging.

---

## Architektur

![Architekturdiagramm](Architekturdiagramm.png)

---

## Tech-Stack

| Komponente    | Technologie                  |
|---------------|------------------------------|
| Framework     | FastAPI 0.135                |
| ORM           | SQLAlchemy 2.0               |
| Datenbank     | MySQL 8.0                    |
| Migrationen   | Alembic                      |
| Auth          | JWT (PyJWT, HS256)           |
| Scheduler     | APScheduler                  |
| QR-Codes      | qrcode + Pillow              |
| Monitoring    | Sentry (optional)            |
| Server        | Uvicorn                      |
| Container     | Docker + Docker Compose      |

---

## Projektstruktur

```
device_management_backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # Route-Handler (auth, geraete, ausleihen, …)
│   │       └── router.py
│   ├── core/
│   │   ├── config.py           # Einstellungen via Pydantic Settings
│   │   ├── scheduler.py        # Hintergrund-Jobs (z. B. überfällige Ausleihen)
│   │   └── security.py         # JWT-Erstellung & Passwort-Hashing
│   ├── crud/                   # Datenbankoperationen
│   ├── db/                     # Session & Base-Klasse
│   ├── models/                 # SQLAlchemy-Modelle
│   ├── schemas/                # Pydantic-Schemas (Request/Response)
│   └── main.py                 # App-Einstiegspunkt
├── alembic/                    # Migrationsskripte
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
└── requirements.txt
```

---

## API-Endpunkte (`/api/v1`)

| Prefix             | Tag             | Beschreibung                             |
|--------------------|-----------------|------------------------------------------|
| `/auth`            | Auth            | Login, Token-Vergabe                     |
| `/geraete`         | Geräte          | CRUD-Operationen, QR-Code-Generierung    |
| `/ausleihen`       | Ausleihen       | Ausleihe starten, verlängern, zurückgeben|
| `/reservierungen`  | Reservierungen  | Reservierungen anlegen & verwalten       |
| `/benutzer`        | Benutzer        | Benutzerverwaltung                       |
| `/audit-logs`      | Audit-Logs      | Nachvollziehbare Aktionshistorie         |

Die interaktive API-Dokumentation ist unter `/api/v1/openapi.json` (Swagger UI: `/docs`, Redoc: `/redoc`) erreichbar.

---

## Datenmodell

### Geräte-Status
`verfügbar` · `ausgeliehen` · `reserviert` · `defekt` · `außer Betrieb`

### Benutzer-Rollen
`Studierende_Mitarbeitende` · `Administrator`

### Ausleihe-Status
`aktiv` · `überfällig` · `abgeschlossen`

### Reservierungs-Status
`aktiv` · `erfüllt` · `storniert`

---

## Lokales Setup (ohne Docker)

### Voraussetzungen
- Python 3.12+
- MySQL-Datenbank

### Installation

```bash
# Repository klonen
git clone <repo-url>
cd device_management_backend

# Virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Umgebungsvariablen

`.env`-Datei im Projektverzeichnis anlegen:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=dein_passwort
DB_NAME=device_management

SECRET_KEY=dein_geheimer_schluessel

CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
BASE_URL=http://localhost:8000

# Optional
SENTRY_DSN=
```

### Datenbank migrieren & Server starten

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Docker-Deployment

Das `docker-compose.yml` startet drei Services:

| Service       | Beschreibung                          | Port (Host) |
|---------------|---------------------------------------|-------------|
| `db`          | MySQL 8.0                             | `3307`      |
| `app`         | FastAPI-Anwendung                     | intern      |
| `phpmyadmin`  | Datenbank-Verwaltungsoberfläche       | intern      |

`app` und `phpmyadmin` sind bewusst **ohne externe Ports** konfiguriert — der Zugriff erfolgt über einen vorgelagerten Reverse Proxy.

### Starten

Alle benötigten Umgebungsvariablen als `.env`-Datei bereitstellen (siehe oben), dann:

```bash
docker compose up -d
```

Der Container führt beim Start automatisch `alembic upgrade head` aus, bevor Uvicorn gestartet wird.

---

## Authentifizierung

Die API verwendet **JWT Bearer Tokens** (HS256, Standard-Gültigkeit: 60 Minuten).

```
POST /api/v1/auth/login
→ { "access_token": "...", "token_type": "bearer" }
```

Das Token wird als `Authorization: Bearer <token>` Header bei geschützten Endpunkten mitgegeben. Benutzer werden über eine `shibboleth_id` identifiziert.

---

## Hintergrund-Jobs

APScheduler läuft als Teil des FastAPI-Lifespan-Kontexts und prüft z. B. automatisch, ob aktive Ausleihen überfällig sind, und aktualisiert deren Status entsprechend.
