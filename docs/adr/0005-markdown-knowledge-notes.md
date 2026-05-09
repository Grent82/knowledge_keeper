# ADR 0005: Markdown-First Knowledge Notes

## Status

Accepted

## Context

Wissensnotizen sollen langfristig portabel, verlinkbar und fuer tools wie Obsidian anschlussfaehig bleiben. Operative Daten wie Rechte oder Fortschritt passen jedoch nicht gut in Dateien.

## Decision

- Wissensnotizen werden spaeter als Markdown gepflegt
- operative Metadaten bleiben in der Datenbank
- Transkripte und Zusammenfassungen koennen zusaetzlich exportiert werden, sind aber nicht primaer dateibasiert

## Consequences

- positive: Wissensbasis bleibt portabel
- positive: operative Daten bleiben robust modellierbar
- negative: Sync zwischen DB und Markdown muss spaeter klar definiert werden
