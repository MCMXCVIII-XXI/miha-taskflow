dev-up:
	docker-compose up -d --build


backend-up:
	docker-compose up backend -d --build


logs:
	docker-compose logs -f


logs-backend:
	docker-compose logs -f backend


test-backend:
	cd backend && uv run pytest


clean:
	docker-compose down -v
	docker system prune -f


down:
	docker-compose down -v

status:
	docker ps


help:
	@echo "Miha-TaskFlow команды:"
	@echo "  make dev-up       ← Запуск всего проекта"
	@echo "  make backend-up   ← Запуск backend"
	@echo "  make test-backend ← Тестирование backend"
	@echo "  make logs-backend ← Логи backend"
	@echo "  make down         ← Остановить все"
	@echo "  make logs         ← Логи всех сервисов"
	@echo "  make clean        ← Остановить всё"
	@echo "  make status       ← docker ps"