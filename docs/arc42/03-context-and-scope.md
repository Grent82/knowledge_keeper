# arc42 03 Context and Scope

## Fachlicher Kontext

Das System interagiert mit:

- Browsern der Nutzer
- lokalem Dateispeicher fuer Medien
- spaeter externen Medienquellen wie YouTube oder Podcasts
- spaeter KI-Providern fuer Transkription, Zusammenfassung und Tagging
- spaeter optionalem Cloud/Object Storage

## Technischer Kontext

Geplante Hauptbausteine:

- React-Frontend
- Django/DRF-Backend
- PostgreSQL
- lokales Medienverzeichnis
- Hintergrundjob-System
- spaeter Vektorindex fuer semantische Suche

## Systemgrenze

Im System:

- Benutzerkonten
- Rollen und Sichtbarkeiten
- Medienmetadaten
- Fortschrittsdaten pro Nutzer
- Transkripte und Zusammenfassungen
- Wissensnotizen

Ausserhalb des Systems:

- eigentliche Medienplattformen externer Quellen
- externe KI-Dienste
- spaeteres Hosting-Setup bei Hostinger
