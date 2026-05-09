# Agent Instructions

Knowledge Keeper ist eine private Wissensplattform fuer Audio, Video und spaetere Markdown-Wissensarbeit. Das Projekt wird agentisch entwickelt und nutzt Beads als einziges Backlog-System.

## Start Here

- Read [docs/product-vision.md](docs/product-vision.md).
- Read [docs/agent-operating-model.md](docs/agent-operating-model.md).
- Follow [docs/engineering-standards.md](docs/engineering-standards.md).
- Use [docs/task-contract.md](docs/task-contract.md) when writing or refining Beads.
- Use the arc42 seed docs under [docs/arc42](docs/arc42).
- Use the workflow docs under [docs/workflows](docs/workflows).
- Use the role docs under [docs/roles](docs/roles) when work naturally falls into architecture, backend, frontend, QA or coordination.
- Check accepted decisions under [docs/adr](docs/adr) before introducing new structure.

## Required Workflow

```bash
bd prime
bd ready
bd show <id>
bd update <id> --claim
```

Do not start substantial implementation before the active bead is claimed.

## Project Guardrails

- Single-user-first, but not single-user-only.
- Progress, status and history are always user-specific.
- Visibility is separate from playback progress.
- External sources and uploaded files are different concepts.
- Markdown is the primary format for knowledge notes, not for operational metadata.
- AI integrations must stay behind replaceable ports/adapters.
- Prefer local-first development; cloud storage and Hostinger deployment come later.

## Quality and Delivery

- Prefer small, testable increments.
- Follow clean architecture boundaries.
- Use TDD for domain and application behavior where practical.
- Record architectural assumptions in `docs/` when they affect future work.
- Create follow-up beads instead of silently expanding scope.
- Run `make quality` before closing substantial work.
- Update `Makefile` quality targets when new runnable tooling is introduced.

## Non-Interactive Shell Commands

Always use non-interactive flags with file operations to avoid hanging on prompts.

```bash
cp -f source dest
mv -f source dest
rm -f file
rm -rf directory
cp -rf source dest
```

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
