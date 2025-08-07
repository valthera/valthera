# Valthera Core

Core utilities and shared code for Valthera Lambda functions.

## Installation

```bash
poetry add valthera-core
```

Or add to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
valthera-core = "^0.1.0"
```

## Usage

```python
from valthera_core import Config, success_response, log_execution_time

@log_execution_time
def lambda_handler(event, context):
    # Your Lambda function code here
    return success_response({"message": "Hello World"})
```

## Available Modules

- **config**: Configuration management for Lambda functions
- **monitoring**: Logging and monitoring utilities
- **responses**: Standardized API response formats
- **validation**: Input validation utilities 