.PHONY: dev-up backend-up logs logs-backend test-backend clean down status lint test dev help

dev-up:
	docker-compose down -v
	docker-compose up -d --build

backend-up:
	docker-compose up backend -d --build

cache-up:
	docker-compose up cache -d --build

db-up:
	docker-compose up db -d --build

infra-up:
	make cache-up
	make db-up

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

test-backend:
	uv sync --group test
	uv run pytest

lint:
	uv sync --group lint
	uv run ruff check .
	uv run mypy app/

format:
	uv sync --group lint
	uv run ruff format .
	uv run ruff check . --fix

lint-all:
	make format
	make lint

test-pg:
	uv sync --group test
	PYTHONPATH=. POSTGRES_DB=taskflow_test uv run pytest --asyncio-mode=auto tests/

test:
	uv sync --group test
	uv run pytest

test-coverage:
	uv sync --group test
	uv run pytest --cov=app --cov-report=term-missing

dev:
	make lint
	make test-backend

clean:
	docker-compose down -v
	docker system prune -f

down:
	docker-compose down -v

status:
	docker ps

help:
	@echo "Miha-TaskFlow:"
	@echo "  make dev-up       Docker всё"
	@echo "  make backend-up   Только backend"
	@echo "  make db-up        Только db"
	@echo "  make test-backend pytest backend"
	@echo "  make logs-backend Логи backend"
	@echo "  make lint         Ruff check + mypy"
	@echo "  make format       Ruff format + mypy"
	@echo "  make lint-all     Ruff check + mypy + Ruff format"
	@echo "  make dev          lint + test"
	@echo "  make down         Остановить"
	@echo "  make clean        Всё чисто"
