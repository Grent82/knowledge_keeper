# Knowledge Graph Linking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add candidate-based knowledge-note linking with TF-IDF and hybrid final link ranking while preserving automatic final note links.

**Architecture:** Introduce a backend-only candidate-link layer between note similarity discovery and final `linked_notes` persistence. Embedding similarity remains, TF-IDF becomes a second deterministic signal, and a hybrid ranking step decides which final edges are written.

**Tech Stack:** Django, Celery tasks, DRF serializers, pytest.

---

### Task 1: Candidate Link Model

**Files:**
- Create: `backend/src/apps/knowledge_notes/migrations/<next>_knowledgenotelinkcandidate.py`
- Modify: `backend/src/apps/knowledge_notes/models.py`
- Test: `backend/tests/test_auto_linking.py`

- [ ] Add failing model/task tests for owner-scoped candidate creation, deduplication, and no self-links.
- [ ] Run targeted tests and confirm failure.
- [ ] Implement `KnowledgeNoteLinkCandidate` with score fields, provenance, status, and uniqueness.
- [ ] Run targeted tests and confirm pass.

### Task 2: Candidate Generation Pipeline

**Files:**
- Modify: `backend/src/apps/knowledge_notes/tasks.py`
- Test: `backend/tests/test_auto_linking.py`

- [ ] Add failing tests showing the auto-link task writes candidates before final links.
- [ ] Run targeted tests and confirm failure.
- [ ] Refactor note-linking task to persist candidate rows from embedding similarity instead of directly writing final links.
- [ ] Re-run targeted tests and confirm pass.

### Task 3: TF-IDF Scorer

**Files:**
- Create: `backend/src/apps/knowledge_notes/tfidf.py`
- Modify: `backend/src/apps/knowledge_notes/tasks.py`
- Test: `backend/tests/test_auto_linking.py`

- [ ] Add failing scorer tests for deterministic TF-IDF similarity on representative note text.
- [ ] Run targeted tests and confirm failure.
- [ ] Implement a minimal TF-IDF scorer over selected note fields.
- [ ] Re-run targeted tests and confirm pass.

### Task 4: Hybrid Ranking and Final Links

**Files:**
- Modify: `backend/src/apps/knowledge_notes/tasks.py`
- Modify: `backend/src/apps/knowledge_notes/views.py`
- Test: `backend/tests/test_auto_linking.py`

- [ ] Add failing tests showing final `linked_notes` are written from combined candidate ranking, not raw embedding threshold alone.
- [ ] Run targeted tests and confirm failure.
- [ ] Implement combined score calculation and final-link materialization.
- [ ] Keep API behavior stable for current consumers.
- [ ] Re-run targeted tests and confirm pass.

### Task 5: Verification and Backlog Hygiene

**Files:**
- Modify: Beads only if implementation reveals new follow-up work

- [ ] Run `make quality`.
- [ ] Update bead status for completed slices.
- [ ] Create follow-up beads only for newly discovered gaps, not for planned later slices already in backlog.
