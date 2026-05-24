# Makefile for Sensor Logging System
# Handles setup, testing, formatting, and cleanup.

.PHONY: help setup format test clean

# Python virtual environment binary path
VENV_BIN := .venv/bin

# Default target listing help instructions
help:
	@echo "========================================================="
	@echo "🌡️  Sensor Logging System Management Console"
	@echo "========================================================="
	@echo "Available commands:"
	@echo "  make setup    - Set up virtual environment and install dependencies"
	@echo "  make format   - Run formatting and styling checks (pre-commit)"
	@echo "  make test     - Run all mocked unit tests locally"
	@echo "  make clean    - Clean python cache files and log/run artifacts"
	@echo "========================================================="

# Set up local python virtual environment
setup:
	@echo "🛠️  Setting up virtual environment..."
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		$(VENV_BIN)/pip install -r requirements.txt; \
		$(VENV_BIN)/pip install yapf pre-commit; \
		$(VENV_BIN)/pre-commit install; \
	else \
		echo "Virtual environment already exists."; \
	fi
	@echo "✅ Environment configured."

# Run formatting and styling checks (pre-commit hooks)
format:
	@echo "🖌️  Running styling and linting pre-commit hooks..."
	@if [ -d ".venv" ]; then \
		$(VENV_BIN)/pre-commit run --all-files; \
	else \
		pre-commit run --all-files; \
	fi
	@echo "✅ Checks complete."

# Run unit tests locally
test:
	@echo "🧪 Running Unit Tests..."
	@python3 -m unittest discover -p "*_test.py"
	@echo "✅ All tests passed!"

# Clean temporary Python cache directories and log directories
clean:
	@echo "🧹 Cleaning cache files and directory artifacts..."
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .pre-commit-config.yaml.cache
	@echo "✅ Cleanup complete."
