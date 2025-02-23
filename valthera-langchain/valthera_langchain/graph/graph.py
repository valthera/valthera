from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph
from valthera.core.graph import BaseGraph, BaseNode
from ..nodes.base import LangChainNode
import logging

logger = logging.getLogger(__name__)

class LangChainGraph(BaseGraph):
    """LangChain-specific graph implementation using LangGraph."""
    
    workflow: StateGraph = Field(default_factory=lambda: StateGraph(Dict[str, Any]))
    nodes: Dict[str, LangChainNode] = Field(default_factory=dict)
    entrypoint_set: bool = Field(default=False)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)

    def add_node(self, node_id: str, node: LangChainNode):
        self.nodes[node_id] = node
        self.workflow.add_node(node_id, node)
    
    def set_entrypoint(self, node_id: str):
        """Set the entrypoint node for the graph."""
        if node_id in self.nodes:
            self.workflow.set_entry_point(node_id)
            self.entrypoint_set = True
        else:
            raise ValueError(f"Node {node_id} not found in graph")
        
    def add_edge(self, from_node: str, to_node: str):
        if self._validate_edge(from_node, to_node):
            self.workflow.add_edge(from_node, to_node)

    def _validate_edge(self, from_node: str, to_node: str) -> bool:
        return from_node in self.nodes and to_node in self.nodes

    def compile(self):
        """Compile the workflow."""
        if not self.entrypoint_set:
            raise ValueError("No entrypoint set for the graph")
        return self.workflow.compile()

    async def execute(self, initial_state: Dict[str, Any]) -> Any:
        """Execute the graph workflow."""
        app = self.compile()
        result = await app.ainvoke(initial_state)
        return result

    def get_node(self, node_id: str) -> LangChainNode:
        """Get a node by its ID."""
        if node_id in self.nodes:
            return self.nodes[node_id]
        raise KeyError(f"Node {node_id} not found in graph")

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.nodes

    def get_nodes(self) -> Dict[str, LangChainNode]:
        """Get all nodes in the graph."""
        return self.nodes

    # Add implementations for abstract methods
    def _execute_node(self, node_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node in the graph.

        Args:
            node_id: The ID of the node to execute
            context: The execution context/state

        Returns:
            Updated context/state after node execution
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in graph")
            
        node = self.nodes[node_id]
        return node.invoke(context)

    def _validate_node(self, node: LangChainNode) -> bool:
        """Validate that a node is properly configured.

        Args:
            node: The node to validate

        Returns:
            bool: True if the node is valid
        """
        # Check if node has required attributes and methods
        if not hasattr(node, 'invoke'):
            return False
            
        # Add any LangChain-specific validation
        if node.chain_type is None and node.model_name is None:
            return False
            
        return True
