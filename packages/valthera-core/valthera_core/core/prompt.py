"""
Developer Documentation: Prompt Model

This module defines the `Prompt` model used within the `valthera_core` framework. 
The `Prompt` class represents a structured input provided by a user to an AI agent.

## Classes

### Prompt (Pydantic Model)
Represents the input query or request given to an AI agent.

#### Attributes:
- `user_id` (Optional[str]): An optional user identifier, useful for context tracking. Default is `None`.
- `text` (str): The actual prompt or query provided by the user.
- `metadata` (Optional[Dict[str, Any]]): Additional context information, such as timestamps, session data, or other relevant metadata. Default is `None`.

#### Configuration:
- `allow_mutation = False`: Ensures immutability, making the model read-only after creation.

"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class Prompt(BaseModel):
    """
    Represents the user input or query given to an AI agent.

    Attributes:
        user_id (Optional[str]): A unique identifier for the user, if applicable.
        text (str): The actual input query provided by the user.
        metadata (Optional[Dict[str, Any]]): Additional metadata, such as timestamps or session details.
    """

    user_id: Optional[str] = None
    text: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Configuration settings for the Pydantic model."""
        allow_mutation = False  # Ensures immutability for safety
