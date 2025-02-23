from pydantic import BaseModel
from typing import Optional, Dict, Any


class Prompt(BaseModel):
    """Represents the user input or query given to an agent."""
    
    user_id: Optional[str] = None  # Optional user identifier for context
    text: str                      # The actual prompt/query from the user
    metadata: Optional[Dict[str, Any]] = None  # Additional context (e.g., timestamp, session data)
    
    class Config:
        """Pydantic config for additional settings."""
        allow_mutation = False  # Ensures immutability for safety
