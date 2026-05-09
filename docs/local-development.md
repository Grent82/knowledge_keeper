# Local Development

## Ziel

Lokale Entwicklung ist die erste Zielumgebung. Hosting und Cloud-Storage kommen spaeter.

## Geplanter Stack

- Node.js fuer das Frontend
- pnpm als Paketmanager
- Python 3.12+ fuer das Backend
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

## Geplante lokale Startreihenfolge

1. Backend-Abhaengigkeiten installieren
2. Frontend-Abhaengigkeiten installieren
3. Datenbank verbinden
4. Backend starten
5. Frontend starten

## Hinweis

Die exakten Startkommandos werden im naechsten Scaffolding-Inkrement verdrahtet, sobald das Django-Projekt und die Vite-App vollstaendig bootfaehig sind.
