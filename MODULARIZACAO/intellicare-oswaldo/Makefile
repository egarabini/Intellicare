.PHONY: install install-dev test lint coverage up down seed

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,ui]"

test:
	pytest tests/ -v

test-quick:
	pytest tests/ -x -q

coverage:
	pytest tests/ --cov=oswaldo --cov-report=term-missing

lint:
	ruff check oswaldo/ tests/

format:
	ruff format oswaldo/ tests/

check: lint test

# Docker
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

# Seed data
seed:
	python scripts/generate_seed.py
	python scripts/load_seed.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
