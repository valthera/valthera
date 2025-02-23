from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any

class Tool(ABC, BaseModel):
    """Abstract base class for tools that agents can use."""

    name: str  # Unique identifier for the tool
    description: str  # Human-readable description of what the tool does

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the tool given some input data."""
        pass

    class Config:
        """Pydantic config for additional settings."""
        allow_mutation = False  # Prevents modification after initialization
