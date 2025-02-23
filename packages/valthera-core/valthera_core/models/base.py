from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"

class ModelParameters(BaseModel):
    """Common parameters for model execution."""
    temperature: float = Field(default=0.7, ge=0, le=1)
    max_tokens: Optional[int] = None
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    """Standard response format for model outputs."""
    text: str
    usage: Dict[str, int]
    model_name: str
    provider: ModelProvider
    metadata: Optional[Dict[str, Any]] = None

class BaseModel(ABC):
    """Abstract base class for model implementations."""

    def __init__(self, model_name: str, provider: ModelProvider):
        self.model_name = model_name
        self.provider = provider

    @abstractmethod
    async def generate(self, prompt: str, params: Optional[ModelParameters] = None) -> ModelResponse:
        """Generate a response from the model."""
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, params: Optional[ModelParameters] = None):
        """Generate a streaming response from the model."""
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that required credentials are available."""
        pass

    @property
    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass
