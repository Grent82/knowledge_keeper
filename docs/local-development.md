# Local Development

## Ziel

Lokale Entwicklung ist die erste Zielumgebung. Hosting und Cloud-Storage kommen spaeter.

## Geplanter Stack

- Node.js fuer das Frontend
- pnpm als Paketmanager
- Python 3.10+ fuer das Backend
- PostgreSQL lokal

## Verzeichnisse

- `frontend/` React + Vite
- `backend/` Django + DRF
- `var/media/` lokaler Medienspeicher

## Umgebung

1. `.env.example` nach `.env` uebernehmen
2. lokale Datenbank anlegen
3. Medienverzeichnis anlegen:

```bash
mkdir -p var/media
```

## Setup

```bash
make frontend-install
make backend-install
mkdir -p var/media
cp .env.example .env
```

## Lokale Startreihenfolge

1. Backend starten

```bash
.venv/bin/python backend/manage.py runserver
```

2. Frontend starten

```bash
pnpm --filter @knowledge-keeper/frontend dev
```

3. Qualitaetschecks ausfuehren

```bash
make quality
pnpm --filter @knowledge-keeper/frontend build
```

## Hinweis

SQLite wird aktuell fuer das lokale Backend-Basissetup verwendet. PostgreSQL bleibt die geplante Ziel-Datenbank fuer die produktive Architektur.
