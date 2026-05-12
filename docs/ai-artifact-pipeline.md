# AI Artifact Pipeline Contracts

## Status

Defined: 2026-05-12. This document is the source of truth for pipeline ordering,
trigger points, idempotency, and reprocessing behavior across all AI artifacts.
All beads that extend the pipeline (kk-0z3, kk-u5e, kk-6b6) must follow these contracts.

---

## Pipeline Overview

```
[Owner action]
      │
      ▼
transcribe_media_item            ← Stage 1: Transcription
      │ (on READY)
      ▼
summarize_transcript(kind=short) ← Stage 2: Short Summary (auto-triggered)
      │ (on READY, future)
      ▼
auto_tag_media_item              ← Stage 3: Auto-Tagging (not yet implemented)
      │ (on READY, future)
      ▼
generate_knowledge_notes         ← Stage 4: AI Knowledge Notes (not yet implemented)
```

On-demand summary kinds (detailed, bullet) are triggered explicitly by the owner,
not automatically chained from stage 1.

---

## Stage 1: Transcription

**Task:** `transcribe_media_item(media_item_id)`
**Trigger:** Owner calls `POST /api/playback/transcribe/` for a media item
**Source:** `MediaAsset.storage_path` for local files; YouTube captions or yt-dlp audio for external sources

### Idempotency

- If a `READY` transcript exists for the media item → return immediately, no new transcript created
- If a `PROCESSING` transcript exists → return HTTP 409, reject the request (checked in view)
- A `PENDING` transcript is upgraded to `PROCESSING` in-place; no duplicate is created

### Failure semantics

- DRM or format unavailable errors → mark `FAILED`, **no retry** (error is permanent)
- All other exceptions → mark `FAILED`, retry up to 3× with 60s backoff (Celery `max_retries=3`)

### Reprocessing

Re-triggering transcription when a `READY` transcript exists is a no-op.
To force re-transcription (not yet in scope), the existing transcript must be deleted first.
Downstream artifacts (summaries, tags, notes) are **not** automatically invalidated when
the transcript record is deleted — this must be handled explicitly if re-transcription is added.

### Output

- `Transcript` record with `status=READY`, `content`, `language_code`, `generated_at`
- `TranscriptSegment` records (existing segments deleted and replaced on each successful run)
- Auto-chains: `summarize_transcript.delay(transcript.id)` with `kind="short"`

---

## Stage 2: Summary Generation

**Task:** `summarize_transcript(transcript_id, kind="short")`
**Trigger (auto):** Chained from stage 1 on transcript READY, kind=short only
**Trigger (on-demand, kk-0z3):** Owner calls a dedicated summary trigger endpoint with explicit kind

**Source of truth:** `transcript.content` (full transcript text)

### Supported kinds

| Kind | Status |
|---|---|
| `short` | Implemented |
| `detailed` | In domain model, not yet triggerable on-demand |
| `bullet` | Not yet in domain — must be added (kk-0z3) |

### Idempotency

**Current behavior (bug):** The task checks for any READY summary on
`(media_item, transcript)` without filtering by `kind`. This means if a `short`
summary exists, requesting `detailed` will silently return without generating anything.

**Required behavior (to be fixed in kk-0z3):** Idempotency must be scoped to
`(media_item, transcript, kind)`. Each kind is independent:
- If a READY summary of the requested kind exists → return immediately (idempotent)
- If a PROCESSING summary of the requested kind exists → return HTTP 409
- If a PENDING summary of the requested kind exists → upgrade to PROCESSING and proceed

### Failure semantics

- All exceptions → mark `FAILED`, retry up to 3× with 60s backoff

### Reprocessing

If the transcript is replaced, existing summaries referencing the old transcript via FK
are not automatically invalidated. If regeneration is needed, the old summaries must be
deleted or the new transcript must produce new summaries explicitly.

### Output

- `Summary` record with `status=READY`, `content`, `kind`, `generated_at`
- Auto-chains: **none currently**; kk-u5e will add tag generation after short summary READY

---

## Stage 3: Auto-Tagging (kk-u5e — not yet implemented)

**Task:** `auto_tag_media_item(media_item_id)` (to be created)
**Trigger:** After the `short` summary reaches `READY` for a media item
**Source of truth:** `Summary.content` where `kind=short`; fallback to `Transcript.content`
  if no short summary is available

### Tag uniqueness constraint

`Tag.name` is globally unique (not owner-scoped). When matching existing tags:
1. Normalize proposed tag name (lowercase, strip whitespace)
2. Look up `Tag.objects.filter(name__iexact=proposed_name).first()`
3. If found → reuse that `Tag` object, regardless of `created_by`
4. If not found → create new `Tag` with `created_by=media_item.owner`
5. Append matched/new tags to `media_item.tags` — never remove existing tags

### Idempotency

Re-running auto-tagging must be safe:
- Do not create duplicate `Tag` records (enforced by `unique=True` on `Tag.name`)
- Do not add a tag to `media_item.tags` if it is already present (`add()` on M2M is idempotent)
- Track whether tagging has run: use an `ArtifactStatus` field or a simple boolean
  `tags_auto_generated` on `MediaItem` (design decision for kk-u5e implementation)

### Output

- 3–5 German tags applied to `media_item.tags`
- Tags reuse existing global `Tag` records where possible

---

## Stage 4: AI Knowledge Note Generation (kk-6b6 — not yet implemented)

**Task:** `generate_knowledge_notes(transcript_id)` (to be created)
**Trigger:** Explicitly by the owner from the transcript/media UI; or optionally after
  stage 3 completes (trigger point to be decided in kk-6b6 implementation)
**Source of truth:** `TranscriptSegment` records (structured, time-stamped);
  fallback to `Transcript.content` if no segments exist

### Note types

Generates notes of at least three kinds:
- `insight` — key claim or mental model from the content
- `action` — concrete step the viewer could take
- `reflection` — open question the content raises

### Idempotency

- A generation run should not create duplicate notes for the same transcript.
- Strategy: check `KnowledgeNote.objects.filter(transcript=transcript, ai_generated=True).exists()`
  before generating. If AI notes exist → skip unless explicitly force-regenerated.
- Force-regeneration is out of scope for kk-6b6; if needed, create a separate bead.

### Manual edit preservation

Once generated, a note's `content_markdown` and `title` are fully editable by the owner.
`ai_generated=True` marks origin but does not lock the note. Editing does not flip
`ai_generated` to `False` — the flag records creation origin, not current state.

### Output

- 3–5 `KnowledgeNote` records with `ai_generated=True`, linked to the transcript and media item

---

## Cross-Cutting Rules

### Manual edits vs AI-generated content

| Field / Object | Editable by owner | AI-generated flag |
|---|---|---|
| `Transcript.content` | No (read-only artifact) | implicit (always AI) |
| `Summary.content` | No (read-only artifact) | implicit |
| `MediaItem.tags` | Yes (add/remove freely) | `tags_auto_generated` bool (proposed) |
| `KnowledgeNote.content_markdown` | Yes | `ai_generated` bool on the note |
| `KnowledgeNote.title` | Yes | `ai_generated` bool on the note |

### Provider abstraction

All AI calls (transcription, summarization, note generation) must go through
the port/adapter pattern established in `apps.playback.ports`. New providers
(tagging, note generation) should define a new `Protocol` in the relevant app's
`ports.py` rather than importing a specific AI SDK directly in task code.

### Celery task naming convention

Tasks follow the pattern `verb_noun(primary_id, **options)`:
- `transcribe_media_item(media_item_id)`
- `summarize_transcript(transcript_id, kind="short")`
- `auto_tag_media_item(media_item_id)` — proposed
- `generate_knowledge_notes(transcript_id)` — proposed

### Error observability

All tasks log at `WARNING` level on expected-but-notable conditions (e.g. no captions found)
and at `ERROR` level on permanent failures (e.g. DRM). Transient failures that trigger
retry do not need an explicit log beyond the exception itself (Celery captures it).

---

## Known Issues to Fix

| Issue | Affected bead |
|---|---|
| `summarize_transcript` idempotency ignores `kind` — existing SHORT summary prevents DETAILED | kk-0z3 |
| No on-demand summary trigger endpoint | kk-0z3 |
| `SummaryKind` missing `bullet` | kk-0z3 |
| No auto-tagging pipeline step | kk-u5e |
| No knowledge note generation service | kk-6b6 |
| `KnowledgeNote` missing `kind` and `ai_generated` fields | kk-6b6 |
