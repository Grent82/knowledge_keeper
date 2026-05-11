# Copilot Instructions

## Session Start

Every session must begin with:

```bash
bd prime      # get workflow context and backlog state
bd ready      # find available work
bd show <id>  # inspect a bead before claiming
bd update <id> --claim  # claim before substantial implementation
```

Do not start substantial implementation before claiming a bead. If no suitable bead exists, create one first (`bd update --new`), then claim it.

## Commands

### Quick checks (before and after any substantial change)

```bash
bd doctor
bd lint
git status --short
```

### Full quality gate (run before closing work)

```bash
make quality   # doctor + beads-lint + lint + typecheck + test + git status
```

### Backend

```bash
# Setup (first time)
python3 -m venv .venv
.venv/bin/pip install -e ./backend pytest pytest-django ruff mypy

# Dev server
.venv/bin/python backend/manage.py runserver

# Tests
.venv/bin/python -m pytest backend/tests                   # all tests
.venv/bin/python -m pytest backend/tests/path/to/test.py   # single test file
.venv/bin/python -m pytest backend/tests -k "test_name"    # single test by name

# Lint / typecheck
.venv/bin/python -m ruff check backend
.venv/bin/python -m mypy --config-file backend/pyproject.toml backend/src
```

### Frontend

```bash
# Setup
pnpm install

# Dev server
pnpm --filter @knowledge-keeper/frontend dev

# Tests (vitest)
pnpm --filter @knowledge-keeper/frontend test              # all tests
pnpm --filter @knowledge-keeper/frontend test -- <pattern> # single file/test

# Lint / typecheck
pnpm --filter @knowledge-keeper/frontend lint
pnpm --filter @knowledge-keeper/frontend typecheck
```

### Both together

```bash
pnpm dev   # starts backend on :8000 and frontend on :3000 (or next free port)
```

## Architecture

**Monorepo** with clean separation:

```
frontend/    React 19 + TypeScript + Vite + React Router 7
backend/     Django 5 + DRF + PostgreSQL (SQLite locally)
docs/        Product, architecture, ADRs, agent workflows
tests/       Cross-cutting tests; later E2E
scripts/     Non-interactive helper scripts
.beads/      Backlog (bd CLI)
```

**Backend layers** (`backend/src/apps/<domain>/`):
- Domain entities and invariants live in `models.py` — no framework logic leaks into domain rules
- Business rules that span multiple models go in `services.py` (see `access_control/services.py`)
- Infrastructure ports/adapters for AI, storage, and jobs are kept replaceable

**Backend apps:**
- `accounts` — custom `User` model extending `AbstractUser` with a `role` field (`owner` / `restricted_user`)
- `media_library` — core domain: `MediaItem`, `MediaAsset`, `ExternalSource`, `Category`, `Tag`
- `playback` — user-specific progress, transcripts and summaries (all keyed on `user + media_item`)
- `access_control` — visibility assignments; `services.py` contains `visible_*_queryset(user)` helpers
- `system` — health checks and bootstrap management commands
- `common` — shared base classes and utilities
- **Background jobs**: Celery handles transcription, summarization, tagging, and later external import jobs

**Key domain invariants:**
- `MediaItem` is the primary user-facing entity; `MediaAsset` holds technical file details separately
- `ExternalSource` (YouTube, podcast, link) is distinct from `MediaAsset` (local upload)
- All playback progress, status and history are scoped to `user + media_item`
- Visibility is separate from playback progress; `Owner` sees all their own content; `RestrictedUser` sees only assigned content
- AI integrations (transcription, summaries) are behind replaceable provider fields — never hardwire a specific provider
- `Transcript` and `Summary` are **media-bound** (not user-bound); `PlaybackProgress` is **user-bound** — do not conflate these
- Storage access must be abstracted behind adapters from the start to allow later migration to Hostinger / S3-compatible cloud (ADR 0004)

**Frontend structure** (`frontend/src/`):
- `features/` — feature modules (e.g., `app-shell/`, `home/`)
- `app/` — routing and app-level setup

## Key Conventions

**Ruff** is the Python linter (`line-length = 100`, rules `E F I B`). Migrations are excluded from lint.

**mypy** runs against `backend/src` only; `manage.py` is excluded.

**`TimestampedModel`** is an abstract base providing `created_at` / `updated_at` — both backend apps define their own copy (not shared yet); use it for new models.

**Visibility queries** must go through `access_control.services.visible_*_queryset(user)` — never filter media items or categories inline in views without using these helpers.

**No new root directories** without a documented architectural decision. Cross-cutting docs go in `docs/`, automation in `scripts/`.

**`var/media/`** is the local media storage path; create it with `mkdir -p var/media`.

**Local DB** is SQLite for dev; PostgreSQL is the production target. Do not rely on SQLite-specific behavior.

**Bootstrap** the owner account with:
```bash
.venv/bin/python backend/manage.py bootstrap_owner --username owner --password secret
```

## Roles

This project uses explicit roles defined in `docs/roles/`. When work naturally falls into one area, adopt that role's perspective and constraints.

| Role | File | Core question |
|---|---|---|
| **Architect** | `docs/roles/architect.md` | Does this belong in Domain, Application, Infrastructure or Interface? Is the decision replaceable later? |
| **Backend** | `docs/roles/backend.md` | Are use cases testable? Is business logic out of framework boundaries? Are API contracts explicit? |
| **Frontend** | `docs/roles/frontend.md` | Are component boundaries clean? Is media display consistent across formats? Is the UX accessible? |
| **QA** | `docs/roles/qa.md` | Are rights and visibility rules correctly isolated per user? Does the player behave stably across formats? |
| **Coordinator** | `docs/roles/coordinator.md` | Is the bead small enough to claim without ambiguity? Are dependencies and scope explicit? |

**When to use multiple roles:** For bead reviews, planning sessions, or any task that spans layers (e.g., a feature touching backend API + frontend UI), reason through each relevant role's concerns before implementing. Surface conflicts between roles as open questions in the bead description rather than silently resolving them.

**Architect role is always active** when introducing new models, new Django apps, new frontend features, or any new `services.py` — check Clean Architecture boundaries and confirm the decision doesn't contradict an existing ADR under `docs/adr/`.

## Definition of Done

A bead is only done when:
1. The bead is updated or closed (`bd close <id>`)
2. The change is locally verified (tests/checks passed)
3. Assumptions and open points are documented in `docs/`
4. Follow-up work exists as a new bead (not left in chat)

## Session Completion

Work is **not** complete until pushed:

```bash
git pull --rebase
bd dolt push
git push
git status   # must show "up to date with origin"
```

Create follow-up beads for remaining work instead of expanding scope silently.
