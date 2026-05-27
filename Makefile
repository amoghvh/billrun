.PHONY: up down logs test load-test clean

up:
	docker-compose up -d
	@echo "BillRun started at http://localhost:8000"
	@echo "API docs: http://localhost:8000/docs"

down:
	docker-compose down -v

logs:
	docker-compose logs -f app

test:
	pytest tests/ -v

load-test:
	./scripts/load_test.sh

clean:
	docker-compose down -v
	docker system prune -f

demo:
	./scripts/demo_commands.sh