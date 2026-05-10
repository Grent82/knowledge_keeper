# Playback and Transcript Model

## Ziel

Diese Schicht speichert:

- nutzergebundenen Wiedergabefortschritt
- Status pro Nutzer und Medium
- Transkripte als operative Daten
- Zusammenfassungen als operative KI-Artefakte

Markdown bleibt für spätere Wissensnotizen reserviert, nicht als Primärspeicher für Fortschritt oder Status.

## Kernobjekte

### PlaybackProgress

- gehört zu genau `user + media_item`
- speichert letzte Position, Prozentfortschritt, Status und letzte Aktivität
- ist die Quelle für "weiter hören/sehen"

### Transcript

- gehört zu genau einem `media_item`
- speichert Volltext, Sprache, Provider und Erzeugungsstatus
- ist relationale Primärspeicherung, nicht Vektor-DB

### TranscriptSegment

- optionale Segmentierung des Transkripts
- speichert Reihenfolge, Zeitfenster und Segmenttext
- spätere Basis für semantische Chunking-/Embedding-Pipelines

### Summary

- gehört zu einem `media_item`
- kann auf ein bestimmtes `transcript` zurückverweisen
- speichert operative Zusammenfassungen getrennt von späteren Wissensnotizen

## Modellierungsregeln

- Fortschritt ist immer pro Nutzer und Medium eindeutig
- Owner und RestrictedUser haben vollständig getrennte Playback-Zustände
- Transkripte und Zusammenfassungen sind mediengebunden, nicht nutzergebunden
- Embeddings/Vektorindex kommen später als abgeleitete Daten, nicht als Primärspeicher

## Statusmodell

### PlaybackStatus

- `not_started`
- `in_progress`
- `paused`
- `completed`

### ArtifactStatus

- `pending`
- `processing`
- `ready`
- `failed`

## Speicherstrategie

- Fortschritt und Status: relationale DB
- Transkript-Volltext: relationale DB
- Segmenttexte: relationale DB
- Zusammenfassungen: relationale DB
- optionale Markdown-Exporte: später als sekundäre Darstellung
- Vektorindex: später aus TranscriptSegment und Summary ableitbar

## Folgearbeit

1. API- und UI-Flows für Fortschrittsaktualisierung
2. KI-Jobmodell für Transcript/Summary-Erzeugung
3. Sichtbarkeitsprüfung für progress-bezogene Endpunkte
4. optionale Markdown-Exportstrategie für Zusammenfassungen
