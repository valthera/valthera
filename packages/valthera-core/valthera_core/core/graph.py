from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Generic, TypeVar, Protocol, runtime_checkable
from pydantic import BaseModel
from enum import Enum
import networkx as nx
import json
import logging

logger = logging.getLogger(__name__)

# Type variables for generic implementations
NodeT = TypeVar('NodeT', bound='BaseNode')
EdgeT = TypeVar('EdgeT', bound='BaseEdge')
ContextT = TypeVar('ContextT')
ResultT = TypeVar('ResultT')


class NodeType(str, Enum):
    AGENT = "agent"
    ROUTER = "router"
    DECISION = "decision"


class BaseNode(BaseModel, ABC):
    """Abstract base class for graph nodes."""
    id: str
    type: NodeType

    @abstractmethod
    def execute(self, context: Any) -> Any:
        """Execute the node's logic with given context."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the node's configuration."""
        pass


class BaseEdge(BaseModel, ABC):
    """Abstract base class for edges."""
    from_node: str
    to_node: str
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the edge configuration."""
        pass


@runtime_checkable
class GraphProtocol(Protocol[NodeT, EdgeT, ContextT, ResultT]):
    """Protocol defining the interface for graph implementations."""
    
    def add_node(self, node: NodeT) -> None:
        ...
    
    def add_edge(self, edge: EdgeT) -> None:
        ...
    
    def validate(self) -> bool:
        ...
    
    def execute(self, context: ContextT) -> ResultT:
        ...


class BaseGraph(BaseModel, ABC, Generic[NodeT, EdgeT, ContextT, ResultT]):
    """Base implementation of the graph interface that satisfies GraphProtocol."""
    
    nodes: Dict[str, NodeT] = {}
    edges: Dict[str, List[str]] = {}
    entry_points: Set[str] = set()
    exit_points: Set[str] = set()
    
    @abstractmethod
    def _validate_node(self, node: NodeT) -> bool:
        """Provider-specific node validation."""
        pass
    
    @abstractmethod
    def _validate_edge(self, from_node: str, to_node: str) -> bool:
        """Provider-specific edge validation."""
        pass
    
    @abstractmethod
    def _execute_node(self, node_id: str, context: ContextT) -> ResultT:
        """Provider-specific node execution."""
        pass

    def validate(self) -> bool:
        """Base validation logic that can be extended by providers."""
        logger.info("Validating graph structure")
        
        # Create NetworkX graph for analysis
        graph = nx.DiGraph()
        for node_id in self.nodes:
            graph.add_node(node_id)
        
        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                if not self._validate_edge(from_node, to_node):
                    return False
                graph.add_edge(from_node, to_node)
        
        # Validate all nodes
        for node in self.nodes.values():
            if not self._validate_node(node):
                return False
        
        # Check reachability
        reachable = set()
        for entry in self.entry_points:
            reachable.update(nx.descendants(graph, entry))
            reachable.add(entry)
            
        if not all(node in reachable for node in self.nodes):
            logger.error("Found unreachable nodes in graph")
            return False
        
        return True

    def execute(self, context: ContextT) -> Dict[str, ResultT]:
        """Base execution logic that can be extended by providers."""
        logger.info("Starting graph execution")
        if not self.validate():
            raise ValueError("Invalid graph structure")
            
        visited = set()
        results: Dict[str, ResultT] = {}
        
        def execute_node(node_id: str) -> ResultT:
            if node_id in visited:
                return results[node_id]
                
            visited.add(node_id)
            result = self._execute_node(node_id, context)
            results[node_id] = result
            
            if node_id in self.edges:
                for next_node in self.edges[node_id]:
                    execute_node(next_node)
                    
            return result
            
        for entry in self.entry_points:
            execute_node(entry)
            
        return results

    def add_node(self, node: NodeT) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: EdgeT) -> None:
        """Add an edge to the graph."""
        if isinstance(edge, BaseEdge):
            if edge.from_node not in self.edges:
                self.edges[edge.from_node] = []
            self.edges[edge.from_node].append(edge.to_node)

    @classmethod
    def from_dict(cls, data: dict) -> 'BaseGraph':
        """Load graph from dictionary format."""
        raise NotImplementedError
    
    @classmethod
    def from_json(cls, json_path: str) -> 'BaseGraph':
        """Load graph from JSON file."""
        raise NotImplementedError
    
    def to_dict(self) -> dict:
        """Convert graph to dictionary format."""
        raise NotImplementedError
    
    def to_json(self, json_path: str) -> None:
        """Save graph to JSON file."""
        raise NotImplementedError
