from typing import Dict, Optional, Any
import logging
from pydantic import BaseModel, Field
from valthera.core.graph import BaseNode, NodeType

logger = logging.getLogger(__name__)

class LangChainNodeConfig(BaseModel):
    """Configuration for LangChain nodes."""
    id: str = Field(default="unnamed", description="ID of the node")
    type: NodeType = Field(default=NodeType.AGENT, description="Type of the node")
    chain_type: Optional[str] = Field(default=None, description="Type of LangChain to use")
    model_name: Optional[str] = Field(default=None, description="Name of the model to use")


class LangChainNode(BaseNode):
    """LangChain-specific node implementation using LangGraph."""
    
    chain_type: Optional[str] = Field(default=None, description="Type of LangChain to use")
    model_name: Optional[str] = Field(default=None, description="Name of the model to use")
    
    def __init__(self, **data):
        config = LangChainNodeConfig(**data)
        node_id = config.chain_type if config.chain_type else config.id
        super().__init__(id=node_id, type=config.type)
        self.chain_type = config.chain_type
        self.model_name = config.model_name
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of BaseNode's execute method."""
        # Convert sync to async execution
        import asyncio
        return asyncio.run(self.invoke(context))

    def validate(self) -> bool:
        """Implementation of BaseNode's validate method."""
        if self.chain_type is None:
            logger.warning("No chain_type specified for LangChainNode")
            return False
        return True
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node execution."""
        return await self.invoke(state)

    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method to implement node logic."""
        return state
