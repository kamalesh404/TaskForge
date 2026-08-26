.PHONY: install dev lint format test typecheck run clean docker-build docker-up

install:
	pip install -e .

dev:
	pip install -e ".[dev,redis,rabbitmq,dashboard,msgpack,lz4]"

lint:
	ruff check src/ cli/ tests/

format:
	ruff format src/ cli/ tests/

test:
	python -m pytest tests/ -v --tb=short

typecheck:
	mypy src/ cli/

run:
	python -m cli.main worker start

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info .mypy_cache .pytest_cache .ruff_cache

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down