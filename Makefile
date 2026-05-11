.PHONY: help doctor beads-lint quality format lint test typecheck backend-check frontend-install backend-install \
        docker-up docker-down docker-logs docker-build docker-prod-build docker-migrate docker-shell

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PNPM := pnpm

help:
	@printf "Targets:\\n"
	@printf "  doctor      Run backlog and repo health checks\\n"
	@printf "  beads-lint  Validate beads hygiene\\n"
	@printf "  quality     Run currently available quality gates\\n"
	@printf "  frontend-install  Install frontend dependencies\\n"
	@printf "  backend-install   Create local venv and install backend dependencies\\n"
	@printf "  format      Run available formatting checks\\n"
	@printf "  lint        Run available lint checks\\n"
	@printf "  test        Run available tests/checks\\n"
	@printf "  typecheck   Run available type checks\\n"

doctor:
	bd doctor

beads-lint:
	bd lint

quality: doctor beads-lint
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	git status --short

format:
	@printf "No formatter wired yet; add after prettier/ruff format decisions are finalized\\n"

lint:
	$(PNPM) --filter @knowledge-keeper/frontend lint
	$(PYTHON) -m ruff check backend

test:
	$(PNPM) --filter @knowledge-keeper/frontend test
	$(PYTHON) backend/manage.py check
	$(PYTHON) -m pytest backend/tests
	$(PYTHON) -m compileall backend

typecheck:
	$(PNPM) --filter @knowledge-keeper/frontend typecheck
	$(PYTHON) -m mypy --config-file backend/pyproject.toml backend/src

frontend-install:
	$(PNPM) install

backend-install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ./backend pytest pytest-django ruff mypy

# ── Docker ─────────────────────────────────────────────────────────────────────
docker-up: ## Start dev stack (postgres, redis, backend, celery, frontend)
	@[ -f .env.docker ] || cp .env.docker.example .env.docker
	docker compose up

docker-down: ## Stop and remove dev containers
	docker compose down

docker-logs: ## Tail logs from all dev containers
	docker compose logs -f

docker-build: ## Rebuild dev images
	docker compose build

docker-migrate: ## Run migrations inside the running backend container
	docker compose exec backend python backend/manage.py migrate

docker-shell: ## Open a shell in the backend container
	docker compose exec backend bash

docker-prod-build: ## Build production images
	docker compose -f docker-compose.prod.yml build
