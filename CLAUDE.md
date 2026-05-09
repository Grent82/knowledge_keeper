# Project Instructions for AI Agents

Use [AGENTS.md](/Users/andre.dittrich/privat/projects/knowledge_keeper/AGENTS.md) as the primary instruction source. This file only adds project-local quick context.

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
## Current Phase

The repository is in planning and bootstrap mode. Prioritize architecture, backlog quality, and clean project setup over premature implementation.

## Current Architectural Direction

- Frontend: React + TypeScript
- Backend: Django + DRF
- Database: PostgreSQL
- Storage: local first, cloud later
- Knowledge notes: Markdown-first
- AI: optional local or API-based adapters from phase 2 onward

## Immediate Expectations

- start every session with `bd prime`
- claim a bead before substantial work
- keep docs aligned with architectural decisions
- do not invent production commands until the stack is actually scaffolded
