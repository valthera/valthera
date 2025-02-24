# valthera-core

## Overview

valthera-core is the core framework for building agent services with a modular design. It leverages modern Python features and Pydantic for data validation.

## Installation

Install the package with Poetry:

```bash
poetry add valthera-core
```

Ensure you have Python ^3.13 installed.

## Features

- Modular model providers (e.g., OpenAI, Ollama)
- Pluggable tool and workflow managers
- Async support for streaming responses
- Built with Pydantic and modern typing practices

## Usage

Create and configure loggers, load configurations, and run model providers as illustrated in our examples:

```python
from valthera_core.utils.logging import setup_logger
logger = setup_logger("example", "example.log")
logger.info("valthera-core started")
```

