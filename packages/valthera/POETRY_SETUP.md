# Poetry Setup Guide for Valthera

This guide explains how to set up and work with the Valthera package using Poetry.

## 🚀 Prerequisites

1. **Install Poetry**: If you don't have Poetry installed, install it first:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Verify Installation**:
   ```bash
   poetry --version
   ```

## 📦 Installation

### Basic Installation
```bash
cd packages/valthera
poetry install
```

### With Development Dependencies
```bash
poetry install --with dev
```

### With Domain-Specific Dependencies
```bash
# Robotics domain
poetry install --with robotics

# Finance domain
poetry install --with finance

# Gaming domain
poetry install --with gaming

# All domains
poetry install --with robotics,finance,gaming
```

## 🛠️ Development Workflow

### 1. Activate Poetry Environment
```bash
# Option 1: Use poetry shell (recommended)
poetry shell

# Option 2: Use poetry run for individual commands
poetry run python -c "from valthera import BC; print('Hello Valthera!')"
```

### 2. Run Tests
```bash
# All tests
poetry run pytest

# Unit tests only
poetry run pytest tests/unit/

# With coverage
poetry run pytest --cov=src/valthera --cov-report=html
```

### 3. Code Quality
```bash
# Format code
poetry run black src/ tests/
poetry run isort src/ tests/

# Lint code
poetry run flake8 src/ tests/
poetry run mypy src/

# Run all checks
poetry run pre-commit run --all-files
```

### 4. Build and Publish
```bash
# Build package
poetry build

# Publish to PyPI (requires authentication)
poetry publish
```

## 🔧 Using Makefile (Poetry-Enabled)

The Makefile has been updated to work with Poetry:

```bash
# Development setup
make dev-setup

# Install dependencies
make install-dev

# Run tests
make test
make test-coverage

# Code quality
make format
make lint
make check

# Add new dependencies
make add-dependency DEP=package_name
make add-dev-dependency DEP=package_name
make add-robotics-dependency DEP=package_name
```

## 📚 Poetry Commands Reference

### Dependency Management
```bash
# Add a new dependency
poetry add package_name

# Add a development dependency
poetry add --group dev package_name

# Add a domain-specific dependency
poetry add --group robotics package_name

# Remove a dependency
poetry remove package_name

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree
```

### Environment Management
```bash
# Activate virtual environment
poetry shell

# Run command in environment
poetry run command

# Show environment info
poetry env info

# Remove virtual environment
poetry env remove python
```

### Package Management
```bash
# Install dependencies
poetry install

# Build package
poetry build

# Publish package
poetry publish

# Show package info
poetry show
```

## 🔍 Troubleshooting

### Common Issues

1. **Poetry not found**: Make sure Poetry is in your PATH
2. **Python version mismatch**: Check your Python version with `poetry env info`
3. **Dependency conflicts**: Use `poetry show --tree` to inspect dependencies

### Reset Environment
```bash
# Remove and recreate virtual environment
poetry env remove python
poetry install
```

### Update Poetry
```bash
poetry self update
```

## 📖 Migration from pip/setuptools

If you were previously using pip/setuptools:

1. **Remove old installation**:
   ```bash
   pip uninstall valthera
   ```

2. **Install with Poetry**:
   ```bash
   poetry install
   ```

3. **Update your scripts** to use `poetry run` or activate the Poetry shell

## 🎯 Best Practices

1. **Always use Poetry shell** for development
2. **Commit poetry.lock** to version control
3. **Use dependency groups** for optional dependencies
4. **Run tests with Poetry** to ensure environment consistency
5. **Use Makefile commands** for common development tasks

## 📝 Example Workflow

```bash
# 1. Clone and setup
git clone <repository>
cd packages/valthera

# 2. Install with development dependencies
poetry install --with dev

# 3. Activate environment
poetry shell

# 4. Run tests
pytest

# 5. Format code
black src/ tests/
isort src/ tests/

# 6. Run linting
flake8 src/ tests/
mypy src/

# 7. Build package
poetry build
```

This Poetry setup provides a modern, reliable way to manage Python dependencies and ensures consistent development environments across different machines.
