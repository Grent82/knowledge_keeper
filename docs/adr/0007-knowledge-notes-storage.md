# ADR 0007: Knowledge Notes Storage and Design

## Status

Accepted

## Context

ADR 0005 established Markdown as the primary format for knowledge notes but left implementation details open. Before implementing the knowledge_notes Django app (kk-02o), design decisions must be made on:

1. Primary storage mechanism
2. Linking strategy between notes
3. Frontend editor approach
4. Relationship to Transcripts and MediaItems

## Decision

### 1. Storage: Database TextField (primary) + optional export

Knowledge notes are stored as Markdown text in a `content_markdown` TextField in the database. This supersedes the file-based interpretation of ADR 0005 for the MVP phase.

Rationale: Simpler API, no filesystem coupling, portable via database backup, Obsidian export can be added later as a separate export endpoint.

### 2. Linking: Explicit M2M relation

`KnowledgeNote.linked_notes` is a ManyToManyField(self, blank=True). No wiki-syntax parser for MVP.

Rationale: Reliable, queryable, no custom parser needed. Wiki-syntax can be added as an enhancement in Phase 4.

### 3. Frontend Editor: Textarea + client-side Markdown preview

A textarea for editing and a preview panel using `react-markdown`. No rich editor (TipTap/CodeMirror) for MVP.

Rationale: Minimal dependency footprint. Rich editor can replace this in Phase 4.

### 4. Transcript/MediaItem relationship

`KnowledgeNote` has nullable FK to `MediaItem` and nullable FK to `Transcript`. Notes can exist independently or be associated with a media item or specific transcript.

### 5. Visibility

Notes are Owner-only. No sharing with restricted_users for MVP.

## Consequences

- positive: Simple, consistent with existing patterns
- positive: No filesystem edge cases for MVP
- positive: Queryable and filterable via DRF
- negative: Not directly file-synced (Obsidian sync requires export step)
- note: ADR 0005 remains valid as a future-direction statement; this ADR clarifies MVP implementation
