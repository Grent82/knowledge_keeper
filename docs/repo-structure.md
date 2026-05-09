# Repo Structure

## Ziel

Das Repository bleibt ein Monorepo mit klarer Trennung zwischen Frontend, Backend, Dokumentation und operativen Hilfsmitteln.

## Struktur

```text
knowledge_keeper/
  frontend/              # React + TypeScript + Vite
  backend/               # Django + DRF + Domain/Application/Infrastructure
  docs/                  # Produkt, Architektur, ADRs, Agent-Workflows
  tests/                 # uebergreifende Testplaetze, spaeter E2E
  scripts/               # nicht-interaktive Hilfsskripte
  .beads/                # Backlog und Agent-Tracking
```

## Begruendung

- Frontend und Backend bleiben technisch eigenstaendig, aber organisatorisch zusammen.
- Architektur- und Entscheidungswissen bleibt repo-nah.
- Agenten koennen Dateigrenzen und Zustaendigkeiten leichter erkennen.
- Deployment kann spaeter getrennt werden, ohne das Entwicklungsmodell zu aendern.

## Frontend

- `frontend/src/`
- `frontend/package.json`
- spaeter Komponenten, Routen, Feature-Module, API-Client

## Backend

- `backend/src/config/` fuer Django-Konfiguration
- `backend/src/apps/` fuer fachliche Module
- spaeter saubere Trennung von Domain, Application und Infrastructure pro Fachbereich

## Tests

- `tests/unit/` fuer sprach- oder paketuebergreifende Unit-Test-Konventionen
- `tests/integration/` fuer Integrations- und API-bezogene Tests
- `tests/e2e/` fuer spaetere UI-Flows

## Regeln

- Keine neue Root-Verzeichnisse ohne begruendete Architekturentscheidung
- Cross-cutting Dokumentation gehoert nach `docs/`
- Projektspezifische Automatisierung gehoert nach `scripts/`
