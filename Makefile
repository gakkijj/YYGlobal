.PHONY: install dev-api dev-web test lint build docker-up docker-down seed-demo seed-demo-llm

install:
	cd services/api && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
	pnpm install

dev-api:
	cd services/api && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-web:
	pnpm --filter @yyglobal/web dev

test:
	cd services/api && .venv/bin/pytest -q
	pnpm --filter @yyglobal/web test

lint:
	cd services/api && .venv/bin/ruff check app tests
	pnpm --filter @yyglobal/web lint

build:
	pnpm --filter @yyglobal/web build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

seed-demo:
	python3 scripts/seed_demo_data.py

seed-demo-llm:
	python3 scripts/seed_demo_data.py --generate-with-llm
