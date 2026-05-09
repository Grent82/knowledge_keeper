# Agent Operating Model

## Zweck

Dieses Projekt wird agentisch entwickelt. Agenten arbeiten nicht rein explorativ, sondern entlang klarer Aufgaben, dokumentierter Annahmen und kleiner, verifizierbarer Inkremente.

## Session Start

Jede Session beginnt mit:

```bash
bd prime
bd ready
```

Dann:

1. passende Bead auswaehlen
2. `bd show <id>` lesen
3. `bd update <id> --claim`
4. erst danach Dateien aendern

## Arbeitsregeln

- Beads ist das einzige Backlog-System.
- Jede groessere Arbeit braucht ein Bead.
- Scope nicht stillschweigend vergroessern.
- Folgearbeit als neues Bead anlegen.
- Entscheidungen mit Auswirkungen auf Architektur oder Domane in den Docs festhalten.
- Vor der Implementierung die betroffenen Grenzen benennen: Domain, Application, Infrastructure, Interface.

## Bevorzugte Arbeitsweise

- klein schneiden
- tests vor oder parallel zur Implementierung anlegen
- zuerst Fachlogik, dann Infrastruktur
- KI-Anbindungen immer hinter Ports/Adaptern kapseln
- Rechte und Fortschritt strikt pro Nutzer modellieren

## Definition of Done

Eine Aufgabe gilt nur dann als abgeschlossen, wenn:

1. das Bead aktualisiert oder geschlossen ist
2. die Aenderung lokal verifiziert wurde
3. Annahmen und offene Punkte dokumentiert wurden
4. Folgearbeit bei Bedarf als neues Bead existiert

## Artefakte

- Produkt- und Architekturentscheidungen liegen unter `docs/`
- Agentenregeln liegen in `AGENTS.md` und `CLAUDE.md`
- Aufgaben und Abhaengigkeiten liegen ausschliesslich in `.beads/`
