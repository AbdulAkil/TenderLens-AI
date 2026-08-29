.DEFAULT_GOAL := help

.PHONY: help build up down logs test lint migrate ingest process embed eval

help:
	@docker compose run --rm api python -c "print('Targets: build up down logs test lint migrate ingest process embed eval')"

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check .
	docker compose run --rm frontend-check npm run lint

migrate:
	docker compose run --rm api alembic upgrade head

ingest:
	docker compose exec api python -m tenderlens.ingestion.cli --query "$(TED_QUERY)" --scope "$(or $(TED_SCOPE),ACTIVE)" --max-notices "$(or $(TED_MAX_NOTICES),250)"

process:
	docker compose exec api python -m tenderlens.documents.cli --tender-id "$(TENDER_ID)"

embed:
	docker compose exec api python -m tenderlens.ai.cli --tender-id "$(TENDER_ID)"

eval:
	docker compose run --rm -v ./:/workspace api python /workspace/scripts/run_evaluation.py
