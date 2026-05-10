# Access Control Model

## Ziel

Knowledge Keeper ist ein privater Wissensspeicher. Das Berechtigungsmodell soll daher klein, explizit und spaeter erweiterbar bleiben.

## Rollen

### Owner

- voller Zugriff auf alle Inhalte
- verwaltet Nutzer, Kategorien, Medien und spaetere Wissensnotizen
- sieht den eigenen Fortschritt, aber nicht automatisch den Fortschritt anderer Nutzer

### RestrictedUser

- sieht nur explizit freigegebene Inhalte
- hat eigenen Fortschritt, eigene Statuswerte und eigenen Verlauf
- sieht keine Owner-Aktivitaet
- darf keine globalen Inhalte oder Sichtbarkeitsregeln verwalten

## Modellierungsregeln

- Authentifizierung und fachliche Sichtbarkeit sind getrennte Konzepte
- Rollen beantworten die Frage, was ein Nutzer grundsaetzlich darf
- Sichtbarkeitsregeln beantworten die Frage, welche Inhalte ein Nutzer sehen darf
- Fortschritt und Status sind immer an `user + media_item` gebunden

## Erste Backend-Entscheidung

- eigenes Django-User-Modell statt spaeterem Migrationsrisiko
- Rollenfeld direkt am User-Modell
- spaetere Sichtbarkeitsregeln auf Kategorie-, Unterkategorie- und Medienebene

## Geplante Sichtbarkeitslogik

### Unrestricted content

- fuer `Owner` immer sichtbar
- fuer `RestrictedUser` nur sichtbar, wenn freigegeben

### Kategorie-Freigaben

- spaeter eigene Zuordnungen zwischen Nutzer und Kategorie
- Vererbung auf Unterkategorien wird explizit modelliert, nicht implizit erraten

### Medien-Freigaben

- direkte Freigabe einzelner Medien unabhaengig von Kategorien moeglich
- spaeter nutzbar fuer Sonderfaelle und externe Quellen

## API-Leitlinien

- Auth via Django/DRF Session oder Token folgt in eigenem Inkrement
- jede API-Antwort mit nutzergebundenen Daten muss auf den angemeldeten Nutzer filtern
- Admin-Rechte werden nicht aus UI-Verhalten abgeleitet, sondern serverseitig geprueft

## Folgearbeit

1. Login- und Session-/Token-Strategie konkretisieren
2. Sichtbarkeitsobjekte fuer Kategorien und Medien modellieren
3. Fortschrittsmodell pro Nutzer und Medium einfuehren
4. API-Berechtigungen fuer Owner vs. RestrictedUser umsetzen
