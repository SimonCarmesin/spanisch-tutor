.PHONY: help env up down logs ps check test lint typecheck frontend frontend-phone frontend-check api-types

help:
	@echo "make env        fehlende Variablen in .env ergänzen"
	@echo "make up         alle Services bauen und starten"
	@echo "make down       Services stoppen"
	@echo "make logs       Logs von backend und litellm"
	@echo "make check      Lint, Typprüfung und Tests des Backends"
	@echo "make frontend   Frontend starten (http://localhost:5173)"
	@echo "make frontend-phone  Frontend im WLAN erreichbar machen (fürs Handy)"
	@echo "make api-types  TypeScript-Typen aus der Backend-API neu erzeugen"

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

frontend:
	cd frontend && npm install && npm run dev

frontend-phone:
	cd frontend && npm install && npm run dev:phone

frontend-check:
	cd frontend && npm run typecheck && npm test && npm run build

api-types:
	cd backend && uv run python ../scripts/export-openapi.py ../frontend/openapi.json
	cd frontend && npm run api:types
