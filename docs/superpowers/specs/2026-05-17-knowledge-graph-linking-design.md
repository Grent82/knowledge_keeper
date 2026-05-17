# Knowledge Graph Linking Design

## Context

Knowledge notes currently create final graph links too early. The backend task
`link_notes_by_principle` computes embedding similarity over
`deeper_principle` and writes matching notes directly into `linked_notes`.
That gives a cheap first pass, but it leaves no explicit space for alternate
signals, later reranking, or debugging why a relationship exists.

The user wants to keep final automatic links, but only after a stronger
pipeline:

- embeddings stay in the system
- TF-IDF is added as a second mathematical signal
- candidate links become an explicit intermediate layer
- KI reranking may be added later on top candidates only

## Decision

We will move knowledge-note linking to a staged pipeline:

1. generate candidate links from the current note to owner-scoped peer notes
2. score candidates with embedding similarity
3. score the same candidates with TF-IDF similarity
4. compute a deterministic combined score
5. write final `linked_notes` only from ranked candidates above a final
   threshold

This keeps final automatic links while making the graph pipeline inspectable
and extensible.

## Data Model

Add a new candidate model:

- `KnowledgeNoteLinkCandidate`
- `source_note`
- `target_note`
- `embedding_score`
- `tfidf_score`
- `combined_score`
- `provenance`
- `status`
- `created_at`
- `updated_at`

Constraints:

- owner consistency is enforced by task logic
- no self-links
- unique candidate per `(source_note, target_note, provenance)`

`linked_notes` remains the final relation used by current API consumers.

## Pipeline

### Candidate generation

The current `link_notes_by_principle` task becomes a pipeline entrypoint:

- load the anchor note
- skip when no usable linking text exists
- gather owner-scoped candidates
- calculate embedding score
- persist or update candidate rows

At this stage, no final graph edge is written yet.

### TF-IDF scoring

Candidate scoring uses a deterministic TF-IDF scorer over selected note text.
The initial text basis should be:

- `title`
- `summary_sentence`
- `core_insight`
- `deeper_principle`

This gives a more transparent lexical comparison than full markdown bodies and
avoids overweighting long note content.

### Hybrid ranking

Combined score is deterministic and documented. Initial version:

- `combined_score = 0.7 * embedding_score + 0.3 * tfidf_score`

This preserves the current semantic bias while adding a classical baseline.
The weight can later move into settings if needed, but it should start as code
constant to keep the first slice small.

### Final edge writing

After candidate scoring, the pipeline writes final `linked_notes` for
candidates whose `combined_score` reaches the final threshold.

This keeps the existing user-facing concept of automatic related notes while
changing how the system decides to create them.

## API Impact

Initial implementation should keep existing API behavior stable:

- `linked_notes` stays serialized
- related-note endpoints may continue to read final links or compute rankings
  as they do today

The candidate layer is primarily backend infrastructure in this round.

## Failure Handling

- embedding provider failure: skip candidate generation/finalization for that
  run
- TF-IDF failure: fail the candidate ranking path and avoid writing new final
  links from incomplete data
- duplicate candidate generation: update existing rows, do not multiply rows

The system should degrade by producing fewer links, not corrupted or misleading
graph edges.

## Testing Strategy

Implementation should proceed in this order:

1. candidate model and persistence tests
2. candidate-generation task tests
3. TF-IDF scorer tests
4. hybrid ranking tests
5. final-link materialization tests

Tests must cover:

- owner scoping
- no self-links
- deduplication
- deterministic scoring
- final links created only after combined ranking

## Follow-up

- optional KI reranking over top candidate links only
- possible future typed edges instead of undifferentiated `linked_notes`
- possible user review/confirmation layer
