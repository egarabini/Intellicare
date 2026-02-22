.PHONY: install test coverage lint format typecheck check clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=florence --cov-report=term-missing

lint:
	ruff check florence/ tests/

format:
	ruff format florence/ tests/

typecheck:
	mypy florence/

check: lint typecheck test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
