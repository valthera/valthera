.PHONY: help install install-dev install-robotics install-finance install-gaming test test-unit test-integration lint format clean build docs examples

help:  ## Show this help message
	@echo "Valthera Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	poetry install

install-dev:  ## Install with development dependencies
	poetry install --with dev

install-robotics:  ## Install with robotics domain dependencies
	poetry install --with robotics

install-finance:  ## Install with finance domain dependencies
	poetry install --with finance

install-gaming:  ## Install with gaming domain dependencies
	poetry install --with gaming

install-all:  ## Install with all domain dependencies
	poetry install --with robotics,finance,gaming

test:  ## Run all tests
	poetry run pytest

test-unit:  ## Run unit tests only
	poetry run pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	poetry run pytest tests/integration/ -v

test-robotics:  ## Run robotics domain tests
	poetry run pytest tests/ -m robotics -v

test-finance:  ## Run finance domain tests
	poetry run pytest tests/ -m finance -v

test-gaming:  ## Run gaming domain tests
	poetry run pytest tests/ -m gaming -v

test-coverage:  ## Run tests with coverage report
	poetry run pytest --cov=src/valthera --cov-report=html --cov-report=term-missing

lint:  ## Run linting checks
	poetry run flake8 src/ tests/
	poetry run mypy src/

format:  ## Format code with black and isort
	poetry run black src/ tests/
	poetry run isort src/ tests/

format-check:  ## Check if code is properly formatted
	poetry run black --check src/ tests/
	poetry run isort --check-only src/ tests/

clean:  ## Clean build artifacts
	poetry run python -m pip cache purge
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build the package
	poetry build

docs:  ## Build documentation
	cd docs && make html

examples:  ## Run example scripts
	@echo "Running robotics example..."
	poetry run python examples/robotics/robot_manipulation.py
	@echo ""
	@echo "Running finance example..."
	poetry run python examples/finance/trading_bot.py

check:  ## Run all quality checks
	format-check
	lint
	test-unit

pre-commit:  ## Install pre-commit hooks
	poetry run pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	poetry run pre-commit run --all-files

dev-setup:  ## Set up development environment
	poetry install --with dev
	poetry run pre-commit install
	@echo "Development environment setup complete!"

ci:  ## Run CI checks
	format-check
	lint
	test-coverage
	@echo "CI checks completed successfully!"

shell:  ## Activate Poetry shell
	poetry shell

add-dependency:  ## Add a new dependency (usage: make add-dependency DEP=package_name)
	poetry add $(DEP)

add-dev-dependency:  ## Add a new development dependency (usage: make add-dev-dependency DEP=package_name)
	poetry add --group dev $(DEP)

add-robotics-dependency:  ## Add a new robotics dependency (usage: make add-robotics-dependency DEP=package_name)
	poetry add --group robotics $(DEP)

add-finance-dependency:  ## Add a new finance dependency (usage: make add-finance-dependency DEP=package_name)
	poetry add --group finance $(DEP)

add-gaming-dependency:  ## Add a new gaming dependency (usage: make add-gaming-dependency DEP=package_name)
	poetry add --group gaming $(DEP)

update:  ## Update all dependencies
	poetry update

lock:  ## Update poetry.lock file
	poetry lock

publish:  ## Publish to PyPI (requires authentication)
	poetry publish

show-deps:  ## Show all dependencies
	poetry show --tree
