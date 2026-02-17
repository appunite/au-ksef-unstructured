.PHONY: install dev test test-cov lint format typecheck docker-build docker-run clean

install:
	uv sync

dev:
	uv run uvicorn src.app.main:app --reload

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

docker-build:
	docker build -t au-ksef-unstructured .

docker-run:
	docker run -p 8080:8080 --env-file .env au-ksef-unstructured

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	rm -rf htmlcov .coverage
