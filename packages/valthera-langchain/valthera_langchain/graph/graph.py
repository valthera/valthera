from typing import Dict, Any, Optional, Set
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph import StateGraph
from valthera_core.core.graph import BaseGraph, BaseNode
import logging
import json

logger = logging.getLogger(__name__)

class WorkflowNode(BaseModel):
    """Configuration model for a workflow node."""
    id: str
    chain_type: str
    model_name: str
    type: str

class WorkflowEdge(BaseModel):
    """Configuration model for a workflow edge."""
    from_: str = Field(alias='from')
    to: str

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=None
    )

class WorkflowConfig(BaseModel):
    """Configuration model for the complete workflow."""
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]

class GraphConfig(BaseModel):
    """Top-level configuration model for the graph."""
    workflow: WorkflowConfig
    entrypoint: str
    initial_state: Dict[str, Any]

class LangChainNode(BaseNode):
    """Base class for LangChain nodes in the workflow."""
    id: str = Field(...)  # required field
    chain_type: Optional[str] = Field(default=None)
    model_name: Optional[str] = Field(default=None)
    type: str = Field(default="agent")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the node's operation on the given context."""
        logger.info(f"Executing {self.type} node '{self.id}' with chain_type={self.chain_type}")
        result = await self.invoke(context)
        logger.info(f"Node '{self.id}' execution completed")
        return result

    def validate(self) -> bool:
        """Validate the node's configuration."""
        if self.chain_type is None and self.model_name is None:
            return False
        return True

    async def invoke(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the node's operation."""
        logger.info(f"Invoking {self.type} node '{self.id}' with context: {context}")
        return context

class LangChainGraph(BaseGraph):
    """LangChain-specific graph implementation using LangGraph."""
    
    workflow: StateGraph = Field(default_factory=lambda: StateGraph(Dict[str, Any]))
    nodes: Dict[str, LangChainNode] = Field(default_factory=dict)
    edges_mapping: Dict[str, Set[str]] = Field(default_factory=dict)  # Internal edges tracking
    entrypoint_set: bool = Field(default=False)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def edges(self) -> Dict[str, Set[str]]:
        """Get the current edge mapping."""
        return self.edges_mapping

    def __init__(self, **data):
        """Initialize the graph with optional configuration data."""
        # Extract edges before parent initialization to avoid validation error
        edges_config = data.pop("edges", [])
        
        super().__init__(**data)
        
        # Extract nodes config
        nodes_config = data.get("nodes", {})
        
        # Initialize nodes
        for node_id, node_data in nodes_config.items():
            node = LangChainNode(**node_data)
            self.add_node(node_id, node)
            
        # Initialize edges from configuration
        for edge in edges_config:
            if isinstance(edge, dict):
                self.add_edge(edge.get("from"), edge.get("to"))
            elif isinstance(edge, (list, tuple)) and len(edge) == 2:
                self.add_edge(edge[0], edge[1])

    def add_node(self, node_id: str, node: LangChainNode):
        """Add a node to the graph."""
        if not self._validate_node(node):
            raise ValueError(f"Invalid node configuration for {node_id}")
        
        self.nodes[node_id] = node
        self.workflow.add_node(node_id, node.execute)
        
        # Initialize empty edge set for new node
        if node_id not in self.edges_mapping:
            self.edges_mapping[node_id] = set()
    
    def set_entrypoint(self, node_id: str):
        """Set the entrypoint node for the graph."""
        if node_id in self.nodes:
            self.workflow.set_entry_point(node_id)
            self.entrypoint_set = True
        else:
            raise ValueError(f"Node {node_id} not found in graph")
        
    def add_edge(self, from_node: str, to_node: str):
        """Add a directed edge between two nodes."""
        if not from_node or not to_node:
            raise ValueError("Both from_node and to_node must be specified")
            
        if self._validate_edge(from_node, to_node):
            self.edges_mapping[from_node].add(to_node)
            self.workflow.add_edge(from_node, to_node)
        else:
            raise ValueError(f"Invalid edge: {from_node} -> {to_node}")

    def _validate_edge(self, from_node: str, to_node: str) -> bool:
        """Validate that an edge can be created between the specified nodes."""
        return from_node in self.nodes and to_node in self.nodes

    def compile(self):
        """Compile the workflow into an executable form."""
        if not self.entrypoint_set:
            raise ValueError("No entrypoint set for the graph")
        return self.workflow.compile()

    async def execute(self, initial_state: Dict[str, Any]) -> Any:
        """Execute the graph workflow."""
        app = self.compile()
        result = await app.ainvoke(initial_state)
        return result

    def get_node(self, node_id: str) -> LangChainNode:
        """Retrieve a node by its ID."""
        if node_id in self.nodes:
            return self.nodes[node_id]
        raise KeyError(f"Node {node_id} not found in graph")

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.nodes

    def get_nodes(self) -> Dict[str, LangChainNode]:
        """Get all nodes in the graph."""
        return self.nodes

    def get_edges(self) -> Dict[str, Set[str]]:
        """Get all edges in the graph."""
        return self.edges_mapping

    def _execute_node(self, node_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node in the graph."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in graph")
        node = self.nodes[node_id]
        return node.execute(context)

    def _validate_node(self, node: LangChainNode) -> bool:
        """Validate that a node is properly configured."""
        return node.validate()

    @classmethod
    def from_json(cls, json_data: dict) -> 'LangChainGraph':
        """Create a LangChainGraph instance from a JSON configuration."""
        # Validate the input configuration
        config = GraphConfig.parse_obj(json_data)
        
        # Create nodes configuration
        nodes_config = {}
        for node in config.workflow.nodes:
            nodes_config[node.id] = {
                "id": node.id,
                "chain_type": node.chain_type,
                "model_name": node.model_name,
                "type": node.type
            }
            
        # Create edges configuration
        edges_config = []
        for edge in config.workflow.edges:
            edges_config.append({
                "from": edge.from_,
                "to": edge.to
            })
            
        # Create graph instance with nodes and edges
        graph = cls(nodes=nodes_config, edges=edges_config)
        
        # Set the entrypoint
        graph.set_entrypoint(config.entrypoint)
        
        return graph