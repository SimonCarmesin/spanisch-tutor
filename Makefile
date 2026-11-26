.PHONY: help env up down logs ps check test lint typecheck

help:
	@echo "make env        fehlende Variablen in .env ergänzen"
	@echo "make up         alle Services bauen und starten"
	@echo "make down       Services stoppen"
	@echo "make logs       Logs von backend und litellm"
	@echo "make check      Lint, Typprüfung und Tests des Backends"

env:
	./scripts/init-env.sh

up:
	docker compose up --build -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f backend litellm

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

typecheck:
	cd backend && uv run mypy

test:
	cd backend && uv run pytest

check: lint typecheck test
