.PHONY: install install-dev test lint format typecheck coverage clean

# Instalacao
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testes
test:
	pytest tests/ -v

test-quick:
	pytest tests/ -x -q

coverage:
	pytest tests/ --cov=intellicare_core --cov-report=term-missing --cov-report=html

# Qualidade de codigo
lint:
	ruff check intellicare_core/ tests/

format:
	ruff format intellicare_core/ tests/

typecheck:
	mypy intellicare_core/

# Tudo junto
check: lint typecheck test

# Limpeza
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
