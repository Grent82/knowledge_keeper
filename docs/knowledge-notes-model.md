# Knowledge Notes Model

## Status

Inventory completed: 2026-05-12. Aligns backlog and beads with actual implementation.
Supersedes any backlog descriptions that implied the model does not exist yet.

---

## What Exists (as of 2026-05-12)

### App: `apps.knowledge_notes`

Fully scaffolded Django app at `backend/src/apps/knowledge_notes/`.

### Model: `KnowledgeNote`

```python
class KnowledgeNote(models.Model):
    owner           = ForeignKey(User, CASCADE, related_name="knowledge_notes")
    title           = CharField(max_length=255)
    content_markdown = TextField(blank=True)
    media_item      = ForeignKey(MediaItem, SET_NULL, null=True, blank=True)
    transcript      = ForeignKey(Transcript, SET_NULL, null=True, blank=True)
    linked_notes    = ManyToManyField("self", blank=True, symmetrical=False)
    created_at      = DateTimeField(auto_now_add=True)
    updated_at      = DateTimeField(auto_now=True)
```

Ordering: `-updated_at`. Migration: `0001_initial`.

### API

- **ViewSet:** `KnowledgeNoteViewSet` — full CRUD (`ModelViewSet`)
- **Permissions:** `IsAuthenticated + IsOwnerRole` (owner-only, no restricted_user access)
- **Filtering:** `?media_item=<id>` and `?transcript=<id>` query params
- **Serializer fields:** `id`, `owner` (read-only), `title`, `content_markdown`, `media_item`,
  `transcript`, `linked_notes`, `created_at`, `updated_at`
- **URL:** registered under `SimpleRouter` with `trailing_slash=False`

### Aligned with ADRs

- **ADR 0005:** Notes stored as Markdown text in `content_markdown` ✓
- **ADR 0007:** Database primary storage, nullable FK to MediaItem and Transcript,
  M2M self-link, owner-only visibility ✓

---

## Gaps for AI-Generated Notes (kk-6b6)

The existing model covers manual note creation completely. The following additions
are required before AI-generated knowledge notes can be implemented:

### 1. `kind` field — note type classification

```python
class NoteKind(models.TextChoices):
    INSIGHT    = "insight",    "Insight"
    ACTION     = "action",     "Action"
    REFLECTION = "reflection", "Reflection"
    QUESTION   = "question",   "Question"
    GENERAL    = "general",    "General"
```

- Default: `GENERAL` (ensures backward compatibility with existing manual notes)
- Required for: grouping AI-generated notes by type, filtering in UI

### 2. `ai_generated` field

```python
ai_generated = BooleanField(default=False)
```

- `False` for all existing manual notes (migration default)
- `True` for any note created by the generation service
- Purpose: allows UI to distinguish AI vs manual notes, surfaces edit affordance

### 3. Generation service

A service in `apps.knowledge_notes` (or `apps.playback` if pipeline-integrated)
that takes a `Transcript` and produces 3–5 `KnowledgeNote` records with
`ai_generated=True`. Source preference: transcript segments (structured),
fallback to `transcript.content` (plain text).

The service must **not** copy summary content verbatim. It should derive:
- **Insight** notes: key claims or mental models from the content
- **Action** notes: concrete steps the viewer could take
- **Reflection** notes: open questions the content raises

### 4. Serializer update

Expose `kind` and `ai_generated` in `KnowledgeNoteSerializer`. `ai_generated`
should be read-only from the API (only the service sets it). `kind` is
writable by the owner.

---

## Relationship to Other Models

```
MediaItem ──< KnowledgeNote >── Transcript
                    │
                    └── linked_notes (M2M self)
```

- A note can exist without a media_item or transcript (standalone note)
- A note with `transcript` set is derived from that specific transcription run
- `linked_notes` is non-symmetrical: `note_a → note_b` does not imply `note_b → note_a`

---

## Out of Scope (deferred)

- Sharing notes with `restricted_user` — owner-only for MVP (ADR 0007)
- Wiki-syntax `[[link]]` auto-linking — deferred to Phase 4 (ADR 0007)
- Obsidian export — planned as a separate endpoint, not part of this model
- Human-in-the-loop review flow for AI-generated notes — separate bead if needed
