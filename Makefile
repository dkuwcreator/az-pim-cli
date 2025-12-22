.PHONY: help smoke test lint format typecheck install clean

help:
@echo "Available targets:"
@echo "  smoke      - Run smoke test (basic validation)"
@echo "  test       - Run full test suite"
@echo "  lint       - Run linter (ruff)"
@echo "  format     - Format code (ruff)"
@echo "  typecheck  - Run type checking (mypy)"
@echo "  install    - Install package in development mode"
@echo "  clean      - Remove build artifacts"

smoke:
@echo "Running smoke test..."
python scripts/smoke_test.py

test:
@echo "Running test suite..."
pytest --cov=az_pim_cli --cov-report=term

lint:
@echo "Running linter..."
ruff check src/ tests/

format:
@echo "Formatting code..."
ruff format src/ tests/

typecheck:
@echo "Running type checker..."
mypy src/

install:
@echo "Installing in development mode..."
pip install -e ".[dev]"

clean:
@echo "Cleaning build artifacts..."
rm -rf build/ dist/ *.egg-info
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
