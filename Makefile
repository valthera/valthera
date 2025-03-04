# Makefile for building and managing valthera packages

.PHONY: all clean install dev valthera langchain-valthera test

# Default target builds both packages
all: valthera langchain-valthera

# Build valthera package
valthera:
	cd valthera && poetry install
	cd valthera && poetry add --group dev pytest
	cd valthera && poetry run pytest
	cd valthera && poetry build

# Build langchain-valthera package
langchain-valthera:
	cd langchain-valthera && poetry install
	cd langchain-valthera && poetry add --group dev pytest
	cd langchain-valthera && poetry run pytest
	cd langchain-valthera && poetry build

# Clean build artifacts
clean:
	rm -rf valthera/dist
	rm -rf langchain-valthera/dist
	find . -type d -name __pycache__ -o -name "*.egg-info" -o -name ".pytest_cache" | xargs rm -rf

# Install both packages
install:
	cd valthera && poetry install
	cd langchain-valthera && poetry install

# Development setup
dev:
	cd valthera && poetry install
	cd langchain-valthera && poetry install

# Run tests
test: dev
	cd valthera && poetry run pytest
	cd langchain-valthera && poetry run pytest

# Show help
help:
	@echo "Available targets:"
	@echo "  all               - Build both packages (default)"
	@echo "  valthera          - Install dependencies, run tests and build valthera package"
	@echo "  langchain-valthera - Install dependencies, run tests and build langchain-valthera package"
	@echo "  install           - Install both packages"
	@echo "  dev               - Install both packages with development dependencies"
	@echo "  clean             - Remove build artifacts"
	@echo "  test              - Run tests for both packages (installs dependencies first)"
