.PHONY: dev-up backend-up logs logs-backend test-backend clean down status lint test dev help cache-up db-up es-up infra-up format lint-all test-integration test-integration-coverage test-integration-coverage-before-fall test-unit test-unit-coverage pre-commit pre-commit-install pre-commit-fix ci-check

dev-up: ## Start full Docker project (down + up --build)
	docker-compose down -v
	docker-compose up -d --build

backend-up: ## Start backend only (up --build)
	docker-compose up backend -d --build

cache-up: ## Start cache only
	docker-compose up cache -d --build

db-up: ## Start database only
	docker-compose up db -d --build

es-up: ## Start elasticsearch only
	docker-compose up elasticsearch -d --build

celery: ## Start celery only
	docker-compose up celery-worker -d --build
	docker-compose up celery-beat -d --build
	docker-compose up flower -d --build

infra-up: ## Start infrastructure (cache + db + es)
	make cache-up
	make db-up
	make es-up
	make celery

logs: ## Show all services logs (follow)
	docker-compose logs -f

logs-backend: ## Show backend logs (follow)
	docker-compose logs -f backend

lint: ## Code linting (ruff check + mypy)
	uv sync --group lint
	uv run ruff check .
	uv run mypy app/

format: ## Code formatting (ruff format + check --fix)
	uv sync --group lint
	uv run ruff format .
	uv run ruff check . --fix

lint-all: ## Full linting + format (format + lint)
	make format
	make lint

test-integration: ## Integration tests (pytest tests/integration/)
	uv sync --group test
	POSTGRES_DB=taskflow_test PYTHONPATH=. uv run pytest tests/integration/ --asyncio-mode=auto

test-unit: ## Unit tests (pytest tests/unit/)
	uv sync --group test
	PYTHONPATH=. uv run pytest tests/unit/ --asyncio-mode=auto

test-unit-coverage: ## Unit tests with coverage (pytest --cov)
	uv sync --group test
	PYTHONPATH=. uv run pytest tests/unit/ --asyncio-mode=auto --cov=app --cov-report=term-missing

test-integration-coverage: ## Integration tests with coverage (pytest --cov)
	uv sync --group test
	PYTHONPATH=. POSTGRES_DB=taskflow_test uv run pytest tests/integration/ --asyncio-mode=auto --cov=app --cov-report=xml --cov-report=term-missing

test-integration-coverage-before-fall: ## Integration tests with coverage before fall
	uv sync --group test
	PYTHONPATH=. uv run pytest -x tests/unit/ --asyncio-mode=auto --cov=app --cov-report=xml --cov-report=term-missing
	PYTHONPATH=. POSTGRES_DB=taskflow_test uv run pytest tests/integration/ -x --asyncio-mode=auto --cov=app --cov-report=xml --cov-report=term-missing

make test-e2e:
	uv sync --group test
	PYTHONPATH=. POSTGRES_DB=taskflow_test uv run pytest tests/e2e/ --asyncio-mode=auto

test-backend: ## pytest all tests (unit + integration)
	make test-unit test-integration test-e2e
	
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-fix: ## Auto-fix pre-commit issues
	pre-commit run --all-files
	make format

ci-check: ## Full CI check (pre-commit + lint + test)
	make pre-commit
	make lint-all
	make test-backend

dev: ## Development check (pre-commit + lint + test-backend)
	make pre-commit
	make lint
	make test-backend
dev: ## Development check (lint + test-backend)
	make lint
	make test-backend

clean: ## Full cleanup (down -v + prune)
	docker-compose down -v
	docker system prune -f

down: ## Stop all services (down -v)
	docker-compose down -v

status: ## Container status (docker ps)
	docker ps

help: ## Show this help
	@echo ""
	@echo "Miha-TaskFlow Makefile:"
	@echo "======================"
	@awk 'BEGIN {FS = ":.*?##"; \
	    printf "\033[36m%-25s\033[0m \033[33m%s\033[0m\n", "Target", "Description"} \
	    /^[a-zA-Z_-]+:.*?##/ { printf "\033[32m%-25s\033[0m \033[33m%s\033[0m\n", $$1, $$2 } \
	    /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
