# ADR 0003: Access and Visibility Model

## Status

Accepted

## Context

Das System ist primaer privat, soll aber einem eingeschraenkten Zweitnutzer selektiven Zugriff erlauben. Fortschrittsdaten duerfen nicht zwischen Nutzern auslaufen.

## Decision

- Start mit zwei Rollen: `Owner` und `RestrictedUser`
- Fortschritt, Status und Verlauf sind immer pro Nutzer gespeichert
- Sichtbarkeit wird separat auf Kategorien, Unterkategorien und Medien modelliert

## Consequences

- positive: private Nutzung bleibt einfach
- positive: Zweitnutzerfaehigkeit ohne volles Rollenframework
- negative: Rechtepruefung muss frueh sauber modelliert werden
