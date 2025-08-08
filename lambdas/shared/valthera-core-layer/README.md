# Valthera Core Lambda Layer

This directory contains the shared `valthera_core` package that is used across all Lambda functions in the Valthera project.

## Structure

```
lambdas/shared/valthera-core-layer/
└── python/
    └── valthera_core/
        ├── __init__.py
        ├── auth.py
        ├── aws_clients.py
        ├── config.py
        ├── monitoring.py
        ├── responses.py
        └── validation.py
```

## Usage

### In Lambda Functions

Import the shared utilities in your Lambda function:

```python
from valthera_core import get_user_id_from_event
from valthera_core import success_response, error_response
from valthera_core import Config
```

### Available Modules

- **auth.py**: Authentication utilities
- **aws_clients.py**: AWS client configurations
- **config.py**: Configuration management
- **monitoring.py**: Monitoring and logging utilities
- **responses.py**: Standardized API response helpers
- **validation.py**: Input validation utilities

## Building

The layer is automatically built when you run:

```bash
./scripts/build-lambdas.sh
```

This script:
1. Extracts the `valthera_core` wheel from `lambdas/wheels/`
2. Places it in the correct layer structure
3. Builds all Lambda functions with the layer attached

## Deployment

The layer is automatically deployed with your SAM stack. All Lambda functions in `template.yaml` are configured to use this layer.

## Development

To update the layer:

1. Update the `valthera_core` package code
2. Build a new wheel: `python setup.py bdist_wheel`
3. Place the wheel in `lambdas/wheels/`
4. Run `./scripts/build-lambdas.sh`
5. Deploy with `sam deploy --guided` 