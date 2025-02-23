from typing import Dict, Any
import logging
from .base import LangChainNode

logger = logging.getLogger(__name__)

class ProcessingNode(LangChainNode):
    """Example node that processes input data."""
    
    chain_type: str = "processing"
    model_name: str = "gpt-3.5-turbo"
    
    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing node received state: {state}")
        state["processed"] = True
        return state

class FinalNode(LangChainNode):
    """Example node that finalizes the workflow."""
    
    chain_type: str = "final"
    model_name: str = "gpt-3.5-turbo"
    
    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Final node received state: {state}")
        state["completed"] = True
        return state
