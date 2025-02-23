from typing import Dict, Optional, Any, List, Callable, Annotated
from pydantic import BaseModel, Field
from enum import Enum
from typing_extensions import Protocol
from valthera.core.graph import BaseNode, BaseEdge, BaseGraph
from langgraph.graph import Graph, StateGraph
import operator
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LangChainNode:
    """LangChain-specific node implementation using LangGraph."""
    def __init__(self, chain_type: Optional[str] = None, model_name: Optional[str] = None):
        self.chain_type = chain_type
        self.model_name = model_name
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node execution."""
        return await self.invoke(state)

    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method to implement node logic."""
        return state


class LangChainGraph:
    """LangChain-specific graph implementation using LangGraph."""
    
    def __init__(self):
        self.workflow = StateGraph(Dict[str, Any])
        self.nodes: Dict[str, LangChainNode] = {}
        self._entrypoint_set = False

    def add_node(self, node_id: str, node: LangChainNode):
        self.nodes[node_id] = node
        self.workflow.add_node(node_id, node)
    
    def set_entrypoint(self, node_id: str):
        """Set the entrypoint node for the graph."""
        if node_id in self.nodes:
            self.workflow.set_entry_point(node_id)
            self._entrypoint_set = True
        else:
            raise ValueError(f"Node {node_id} not found in graph")
        
    def add_edge(self, from_node: str, to_node: str):
        if self._validate_edge(from_node, to_node):
            self.workflow.add_edge(from_node, to_node)

    def _validate_edge(self, from_node: str, to_node: str) -> bool:
        return from_node in self.nodes and to_node in self.nodes

    def compile(self):
        """Compile the workflow."""
        if not self._entrypoint_set:
            raise ValueError("No entrypoint set for the graph")
        return self.workflow.compile()

    async def execute(self, initial_state: Dict[str, Any]) -> Any:
        """Execute the graph workflow."""
        app = self.compile()
        result = await app.ainvoke(initial_state)
        return result


class ProcessingNode(LangChainNode):
    """Example node that processes input data."""
    
    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing node received state: {state}")
        state["processed"] = True
        return state


class FinalNode(LangChainNode):
    """Example node that finalizes the workflow."""
    
    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Final node received state: {state}")
        state["completed"] = True
        return state


async def main():
    logger.info("Creating new LangChain graph")
    graph = LangChainGraph()
    
    # Create nodes
    processor = ProcessingNode(chain_type="processor", model_name="example")
    finalizer = FinalNode(chain_type="finalizer", model_name="example")
    
    # Add nodes to graph
    logger.info("Adding nodes to graph")
    graph.add_node("processor", processor)
    graph.add_node("finalizer", finalizer)
    
    # Set the entrypoint
    logger.info("Setting entrypoint")
    graph.set_entrypoint("processor")
    
    # Connect nodes
    logger.info("Connecting nodes")
    graph.add_edge("processor", "finalizer")
    
    # Execute graph
    initial_state = {"input": "test data"}
    logger.info(f"Executing graph with initial state: {initial_state}")
    
    try:
        result = await graph.execute(initial_state)
        logger.info(f"Graph execution completed. Final state: {result}")
    except Exception as e:
        logger.error(f"Error during graph execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
