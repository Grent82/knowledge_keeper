# Media Domain Model

## Ziel

Die Mediendomäne bildet die gemeinsame Grundlage für:

- lokale Uploads
- externe Medienquellen
- Kategorisierung und Tags
- spätere Sichtbarkeitsregeln
- Fortschritt, Transkripte und Zusammenfassungen

## Kernobjekte

### Category

- hierarchische Struktur über `parent`
- dient als thematische Einordnung
- später nutzbar für Sichtbarkeitsvererbung

### Tag

- flache, frei kombinierbare Verschlagwortung
- getrennt von Kategorien

### ExternalSource

- beschreibt eine externe Herkunft
- Beispiele: YouTube, Podcast, Web-Link
- kann Provider, URL und externe Referenz-ID tragen

### MediaItem

- zentrale fachliche Einheit
- beschreibt das konsumierbare Objekt aus Nutzersicht
- kann Audio oder Video sein
- kann auf lokales Asset, externe Quelle oder beides verweisen

### MediaAsset

- technische Repräsentation eines lokalen oder direkt abspielbaren Assets
- enthält Speicherpfad, Format, MIME-Type, Dateigröße und optionale Metadaten

## Modellierungsregeln

- `MediaItem` ist die fachliche Hauptentität
- `MediaAsset` hält technische Dateidetails getrennt von fachlichen Metadaten
- `ExternalSource` ist von `MediaAsset` getrennt, weil Herkunft nicht dasselbe ist wie Datei
- Kategorien und Tags hängen an `MediaItem`, nicht an `MediaAsset`

## Normalisierte Wiedergabe

Das Frontend soll Video unabhängig vom Originalformat in einem einheitlichen Player-Container anzeigen.

Deshalb hat `MediaItem` ein `player_display_mode`:

- `uniform`: Standard für einheitliche Darstellung
- `original`: später optional für originalgetreuere Darstellung

Die echten Abmessungen bleiben technische Asset-Metadaten.

## Unterstützte Formate

Startkatalog:

- Video: `mp4`, `webm`, `mov`, `mkv`
- Audio: `mp3`, `m4a`, `aac`, `wav`, `flac`
- unbekannt/sonstige Formate werden nicht ausgeschlossen, aber explizit markiert

## Folgearbeit

1. Sichtbarkeitszuweisungen für Kategorien und Medien
2. Fortschrittsmodell pro Nutzer und Medium
3. Upload- und externe-Import-Flows
4. API-Serialisierung und Admin-Flows
