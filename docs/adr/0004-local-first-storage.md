# ADR 0004: Local-First Storage with Cloud Later

## Status

Accepted

## Context

Die erste Ausbaustufe soll lokal laufen. Spaeter sollen Hosting und Medienstorage auf Hostinger oder S3-kompatiblen Storage wechseln koennen.

## Decision

- Medien werden zuerst lokal gespeichert
- Storage-Zugriff wird ueber Adapter abstrahiert
- Cloud/Object Storage ist eine spaetere Ausbaustufe, kein MVP-Zwang

## Consequences

- positive: schneller lokaler Start
- positive: geringere Komplexitaet im MVP
- positive: spaetere Migration bleibt vorbereitet
- negative: frueh auf Storage-Abstraktion achten
