.PHONY: install test lint docker-up docker-down

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=zilda --cov-report=term-missing

lint:
	ruff check zilda/ tests/
	mypy zilda/

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
