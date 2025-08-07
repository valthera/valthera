# Valthera Core Layer

This Lambda layer contains the core business logic and utilities used across all Valthera Lambda functions.

## Contents

- **auth.py**: Authentication and authorization utilities
- **config.py**: Configuration management
- **validation.py**: Data validation utilities
- **responses.py**: Standardized API response formatting
- **monitoring.py**: Logging and monitoring utilities
- **aws_clients.py**: AWS service client initialization

## Dependencies

This layer uses Poetry for dependency management. Dependencies include:

- boto3: AWS SDK
- requests: HTTP client
- python-dateutil: Date utilities
- pydantic: Data validation
- python-jose: JWT handling

## Building

To build this layer:

```bash
cd lambdas/layers/valthera-core
poetry install
poetry export -f requirements.txt --output requirements.txt --without-hashes
pip install -r requirements.txt -t python/
```

Or use the build script:

```bash
./lambdas/shared/scripts/build-layers.sh
```

## Usage

In your Lambda function, you can import from this layer:

```python
from valthera_core import auth, config, validation, responses

# Use the utilities
user = auth.get_current_user(event)
config_data = config.get_config()
validated_data = validation.validate_input(data)
response = responses.success_response(data)
``` 