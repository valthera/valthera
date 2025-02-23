from typing import Dict, Any
from langgraph.graph import StateGraph
from ..nodes.base import LangChainNode
import logging

logger = logging.getLogger(__name__)

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
