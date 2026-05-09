# Engineering Standards

## Architekturprinzipien

- Clean Architecture
- Clean Code
- testbare Use Cases
- explizite Ports/Adapter fuer Infrastruktur
- spaet bindbare KI-Provider

## Schichten

### Domain

- Entitaeten, Value Objects, Invarianten
- keine Framework-Abhaengigkeiten

### Application

- Use Cases
- Orchestrierung
- Ports zu Storage, KI, Suche, Jobs

### Infrastructure

- Datenbank
- Dateispeicher
- externe Medienimporte
- KI-Provider
- Hintergrundjobs

### Interfaces

- Web UI
- REST API
- Admin UI

## Teststrategie

- Domain: schnell, isoliert, deterministisch
- Application: Use-Case-Tests gegen Ports/Fakes
- Infrastructure: gezielte Integrationstests
- UI: nur fuer kritische Flows

## Modellierungsregeln

- Wiedergabefortschritt ist immer nutzergebunden
- Sichtbarkeit ist getrennt vom Fortschritt
- Externe Quellen sind getrennt von physisch hochgeladenen Dateien
- Markdown ist primaer fuer Wissensnotizen, nicht fuer operative Metadaten

## Qualitaetsziele

- Erweiterbarkeit fuer neue Quellentypen
- austauschbare Transkriptions- und KI-Backends
- einfache Hosting-Migration von lokal zu Hostinger/S3-kompatiblem Storage
- klare Berechtigungsgrenzen
