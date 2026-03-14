.PHONY: install lint format typecheck test test-cov clean all

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	black src/ tests/

typecheck:
	mypy src/

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=murmur --cov-report=term-missing

clean:
	rm -rf __pycache__ .pytest_cache dist/ build/ *.egg-info .coverage

all: install lint typecheck test
