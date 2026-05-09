# ADR 0001: Monorepo Structure

## Status

Accepted

## Context

Knowledge Keeper umfasst Frontend, Backend, Architekturwissen und agentische Prozessartefakte. Die Entwicklung soll lokal starten und spaeter in getrennte Deployments muenden koennen.

## Decision

Wir verwenden ein Monorepo mit getrennten Verzeichnissen fuer Frontend, Backend, Dokumentation, Tests und Skripte.

## Consequences

- positive: einfacher gemeinsamer Kontext fuer Agenten und Menschen
- positive: Dokumentation und Backlog bleiben nah am Code
- positive: spaetere Trennung fuer Deployment bleibt moeglich
- negative: Root-Konfiguration braucht Disziplin
