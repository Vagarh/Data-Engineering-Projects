# Data Engineering Projects - Makefile
# ====================================

.PHONY: help install lint format test security clean docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  make install     - Install development dependencies"
	@echo "  make lint        - Run linters (black, flake8, mypy)"
	@echo "  make format      - Format code with black and isort"
	@echo "  make test        - Run all tests"
	@echo "  make security    - Run security scan with bandit"
	@echo "  make clean       - Clean cache and build files"
	@echo "  make docker-up   - Start all Docker services"
	@echo "  make docker-down - Stop all Docker services"

# Install dependencies
install:
	pip install -r requirements-dev.txt
	pre-commit install

# Lint code
lint:
	@echo "Running Black check..."
	black --check --diff .
	@echo "Running Flake8..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Running MyPy..."
	mypy --ignore-missing-imports . || true

# Format code
format:
	@echo "Formatting with Black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

# Run tests
test:
	@echo "Running tests..."
	pytest -v --tb=short

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term

# Security scan
security:
	@echo "Running Bandit security scan..."
	bandit -r . -x ./tests,./*/tests --skip B101,B104,B108

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

# Docker commands
docker-up:
	@echo "Starting services..."
	@for dir in unified_data_lake_project youtube_trends_pipeline social_sentiment_pipeline security_logs_pipeline ml_feature_store; do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			echo "Starting $$dir..."; \
			docker-compose -f $$dir/docker-compose.yml up -d; \
		fi \
	done

docker-down:
	@echo "Stopping services..."
	@for dir in unified_data_lake_project youtube_trends_pipeline social_sentiment_pipeline security_logs_pipeline ml_feature_store; do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			echo "Stopping $$dir..."; \
			docker-compose -f $$dir/docker-compose.yml down; \
		fi \
	done

# Project-specific commands
unified-up:
	docker-compose -f unified_data_lake_project/docker-compose.yml up -d

youtube-up:
	docker-compose -f youtube_trends_pipeline/docker-compose.yml up -d

sentiment-up:
	docker-compose -f social_sentiment_pipeline/docker-compose.yml up -d

security-up:
	docker-compose -f security_logs_pipeline/docker-compose.yml up -d

feature-store-up:
	docker-compose -f ml_feature_store/docker-compose.yml up -d
