# ADR 0002: Frontend and Backend Stack

## Status

Accepted

## Context

Das Produkt braucht eine Weboberflaeche, Benutzerzugriff, Medienverwaltung, Fortschrittsspeicherung und spaeter KI-nahe Hintergrundjobs.

## Decision

- Frontend: React + TypeScript + Vite
- Backend: Django + Django REST Framework
- Datenbank: PostgreSQL
- Hintergrundjobs: Celery

## Consequences

- positive: gute Basis fuer Content-, Auth- und Admin-lastige Anforderungen
- positive: starke Typisierung und moderne Frontend-Toolchain
- positive: saubere Erweiterung fuer Jobs, KI und Storage
- negative: zwei Runtime-Stacks im lokalen Setup
