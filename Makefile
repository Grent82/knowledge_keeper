.PHONY: help doctor beads-lint quality format lint test typecheck

help:
	@printf "Targets:\\n"
	@printf "  doctor      Run backlog and repo health checks\\n"
	@printf "  beads-lint  Validate beads hygiene\\n"
	@printf "  quality     Run currently available quality gates\\n"
	@printf "  format      Placeholder until code scaffold is installed\\n"
	@printf "  lint        Placeholder until code scaffold is installed\\n"
	@printf "  test        Placeholder until code scaffold is installed\\n"
	@printf "  typecheck   Placeholder until code scaffold is installed\\n"

doctor:
	bd doctor

beads-lint:
	bd lint

quality: doctor beads-lint
	git status --short

format:
	@printf "format target not wired yet; implement after frontend/backend scaffold\\n"

lint:
	@printf "lint target not wired yet; implement after frontend/backend scaffold\\n"

test:
	@printf "test target not wired yet; implement after frontend/backend scaffold\\n"

typecheck:
	@printf "typecheck target not wired yet; implement after frontend/backend scaffold\\n"
