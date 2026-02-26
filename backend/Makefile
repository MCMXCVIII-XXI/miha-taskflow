.PHONY: dev-up backend-up logs logs-backend test-backend clean down status lint test dev help

dev-up:
	docker-compose up -d --build

backend-up:
	docker-compose up backend -d --build

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

test-backend:
	cd backend && uv sync --group test && uv run pytest

lint:
	uv sync --group lint && ruff check . && ruff format --check . && mypy .

test:
	make test-backend

dev:
	make lint && make test-backend

clean:
	docker-compose down -v && docker system prune -f

down:
	docker-compose down -v

status:
	docker ps

help:
	@echo "Miha-TaskFlow:"
	@echo "  make dev-up       Docker всё"
	@echo "  make backend-up   Только backend"
	@echo "  make test-backend pytest backend"
	@echo "  make logs-backend Логи backend"
	@echo "  make lint         Ruff + mypy"
	@echo "  make dev          lint + test"
	@echo "  make down         Остановить"
	@echo "  make clean        Всё чисто"
