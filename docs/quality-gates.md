# Quality Gates

## Ziel

Agenten brauchen verifizierbare Rueckmeldung. Deshalb gelten verbindliche lokale Gates.

## Immer vor und nach groesseren Aenderungen

```bash
bd doctor
bd lint
git status --short
```

## Nach dem Scaffolding verbindlich

Sobald Frontend und Backend lauffaehig sind, muessen diese Kommandos gepflegt und genutzt werden:

```bash
make format
make lint
make test
make typecheck
```

## Minimalanforderungen pro Schicht

### Domain und Application

- Unit-Tests
- keine Framework-Kopplung ohne Grund
- deterministische Testdaten

### API und Integration

- Integrations- oder API-Tests fuer vertraglich relevante Flows
- Rechte- und Sichtbarkeitsregeln pruefen

### Frontend

- Typecheck
- Lint
- Tests fuer kritische Nutzerfluesse

## Pull/Session Readiness

Vor Abschluss einer Session:

1. Bead-Status korrekt setzen
2. relevante Checks laufen lassen
3. `git status --short` muss erwartbar sein
4. offene Folgearbeit als Bead anlegen

## Regel

Wenn ein Agent einen notwendigen Check nicht ausfuehren kann, muss das im Abschluss explizit benannt werden.
