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
./scripts/setup.sh
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py bootstrap_owner --username owner --password secret
```

## App starten

```bash
pnpm dev
```

Das startet:

- Backend auf `http://localhost:8000` oder dem naechsten freien Port
- Frontend auf `http://localhost:3000` oder dem naechsten freien Port

`Ctrl+C` beendet beide Prozesse zusammen.

Falls das Frontend auf `3001`, `3002` oder `3003` startet, ist das lokale Django-Setup bereits als vertrauenswuerdige CSRF-Origin vorkonfiguriert.

Der Celery-Worker bleibt vorerst optional und wird separat gestartet.

## Manuelle Alternative

1. Backend starten

```bash
.venv/bin/python backend/manage.py runserver
```

2. Frontend starten

```bash
pnpm --filter @knowledge-keeper/frontend dev
```

3. Celery-Worker starten (optional, benoetigt Redis auf localhost:6379)

```bash
.venv/bin/celery -A config worker --loglevel=info --concurrency=1
```

4. Qualitaetschecks ausfuehren

```bash
make quality
pnpm --filter @knowledge-keeper/frontend build
```

## Hinweis

SQLite wird aktuell fuer das lokale Backend-Basissetup verwendet. PostgreSQL bleibt die geplante Ziel-Datenbank fuer die produktive Architektur.

## Media Storage

By default media files are stored locally under `var/media/`.

To switch to S3-compatible storage (e.g. Hostinger Object Storage or MinIO), set:

```env
MEDIA_STORAGE_PROVIDER=s3
S3_BUCKET=my-bucket
S3_ENDPOINT_URL=https://s3.example.com   # omit for AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=auto
S3_PUBLIC_URL_BASE=https://cdn.example.com   # optional, for public URLs
```

boto3 must be installed: `pip install boto3`
