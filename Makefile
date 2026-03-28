.PHONY: dev lint test seed docker-up docker-down migrate

dev:
	.venv/bin/uvicorn app.main:app --reload --port 8085

lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format:
	.venv/bin/ruff check --fix .
	.venv/bin/ruff format .

test:
	.venv/bin/pytest -v

seed:
	.venv/bin/python -m app.seed

migrate:
	.venv/bin/alembic upgrade head

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
