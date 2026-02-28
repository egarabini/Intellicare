.PHONY: install test lint run docker-up docker-down

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

coverage:
	pytest tests/ -v --cov=wanda --cov-report=term-missing

lint:
	ruff check wanda/ tests/

run:
	uvicorn wanda.api.app:app --reload --port 8000

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
