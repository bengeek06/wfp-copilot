# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

.PHONY: help install install-dev format lint type-check test test-cov test-cov-badge clean run compose-build compose-up compose-down docker-build-dev docker-build-test docker-build-prod docker-test monitoring-up monitoring-down monitoring-logs pre-commit-install pre-commit-run docstring-check docstring-coverage test-integration test-unit test-all

# Default target
help:
	@echo "Available commands:"
	@echo "  make install           - Install production dependencies"
	@echo "  make install-dev       - Install development dependencies"
	@echo "  make format            - Format code with black and isort"
	@echo "  make lint              - Run ruff linter"
	@echo "  make type-check        - Run mypy type checker"
	@echo "  make docstring-check   - Check docstring presence with interrogate"
	@echo "  make docstring-coverage- Generate docstring coverage report"
	@echo "  make test              - Run unit + integration (requires services running)"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests (requires services)"
	@echo "  make test-cov          - Run unit + integration with coverage (requires services)"
	@echo "  make test-cov-badge    - Generate test coverage badge"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run    - Run pre-commit on all files"
	@echo "  make clean             - Remove cache and build artifacts"
	@echo "  make run               - Run development server"
	@echo "  make compose-build     - Build Docker Compose services"
	@echo "  make compose-up        - Start Docker Compose services"
	@echo "  make compose-down      - Stop Docker Compose services"
	@echo "  make docker-build-dev  - Build development Docker image"
	@echo "  make docker-build-test - Build test Docker image"
	@echo "  make docker-build-prod - Build production Docker image"
	@echo "  make docker-test       - Run tests in Docker container"
	@echo "  make check             - Run all quality checks (format, lint, type-check, docstring-check, test)"

# Install production dependencies
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Format code
format:
	@echo "Running isort..."
	isort .
	@echo "Running ruff format..."
	ruff format .
	@echo "✓ Code formatted"

# Lint code
lint:
	@echo "Running ruff..."
	ruff check . --fix
	@echo "✓ Linting complete"

# Type checking
type-check:
	@echo "Running mypy..."
	mypy app/ tests/ --config-file=pyproject.toml
	@echo "✓ Type checking complete"

# Check docstring presence
docstring-check:
	@echo "Running interrogate..."
	interrogate app/ -c pyproject.toml
	@echo "✓ Docstring check complete"

# Generate docstring coverage report
docstring-coverage:
	@echo "Generating docstring coverage report..."
	interrogate app/ -c pyproject.toml --generate-badge docs/assets
	@echo "✓ Badge generated: docs/assets/interrogate_badge.svg"

# Run tests (assumes integration services are already running)
test:
	@echo "Running unit tests..."
	pytest tests/unit/ -v
	@echo ""
	@echo "Running integration tests..."
	pytest tests/integration/ -v --maxfail=0 || [ $$? -eq 5 ] && echo "⚠️  No integration tests yet"
	@echo ""
	@echo "✓ Tests completed"

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v

# Run tests with coverage (unit + integration combined)
test-cov:
	@echo "Running unit tests with coverage..."
	@rm -rf .coverage htmlcov/ coverage.xml
	pytest tests/unit/ -v --cov=app --cov-report=
	@echo ""
	@echo "Flushing Redis to clear rate limiting counters..."
	@docker exec wfp-redis-test redis-cli FLUSHDB > /dev/null 2>&1 || true
	@echo ""
	@echo "Running integration tests with coverage (appending)..."
	pytest tests/integration/ -v --cov=app --cov-append --cov-report=
	@echo ""
	@echo "Generating combined coverage report..."
	coverage report
	coverage html
	coverage xml
	@echo ""
	@echo "✓ Coverage report generated in htmlcov/ and coverage.xml"
	@echo "  Open htmlcov/index.html to view the report"

# Generate test coverage badge
test-cov-badge:
	@echo "Generating test coverage badge..."
	genbadge coverage -i coverage.xml -o docs/assets/coverage_badge.svg
	@echo "✓ Badge generated: docs/assets/coverage_badge.svg"

# Install pre-commit hooks
pre-commit-install:
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

# Run pre-commit on all files
pre-commit-run:
	pre-commit run --all-files

# Clean cache and build artifacts
clean:
	@echo "Cleaning cache and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml
	@echo "✓ Cleaned"

# Run development server
run:
	python run.py

# Docker Compose commands
compose-build:
	@echo "Building Docker Compose services..."
	docker compose -f docker-compose.test.yml build
	@echo "✓ Docker Compose services built"

compose-up:
	@echo "Starting Docker Compose services..."
	docker compose -f docker-compose.test.yml up -d
	@echo "✓ Docker Compose services started"

compose-down:
	@echo "Stopping Docker Compose services..."
	docker compose -f docker-compose.test.yml down
	@echo "✓ Docker Compose services stopped"

# Docker Image commands
docker-build-dev:
	@echo "Building development Docker image..."
	docker build --target development -t wfp-flask-template:dev .
	@echo "✓ Development image built: wfp-flask-template:dev"

docker-build-test:
	@echo "Building test Docker image..."
	docker build --target test -t wfp-flask-template:test .
	@echo "✓ Test image built: wfp-flask-template:test"

docker-build-prod:
	@echo "Building production Docker image..."
	docker build --target production -t wfp-flask-template:prod .
	@echo "✓ Production image built: wfp-flask-template:prod"

docker-test: docker-build-test
	@echo "Running tests in Docker container..."
	docker run --rm wfp-flask-template:test
	@echo "✓ Docker tests completed"

# Quality check (all checks)
check: format lint type-check docstring-check test
	@echo "✓ All quality checks passed"
