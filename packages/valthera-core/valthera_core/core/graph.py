"""
Developer Documentation: Graph Base Classes

This module defines the core structures for a directed graph framework used in `valthera_core`. 
It provides base classes for nodes, edges, and the graph itself, supporting execution and validation.

## Classes

### NodeType (Enum)
Defines different types of nodes in the graph.

- `AGENT`: Represents an agent node.
- `ROUTER`: Represents a routing node.
- `DECISION`: Represents a decision-making node.

### BaseNode (Abstract Base Class)
Represents a node within the graph, designed to be extended for specific behaviors.

#### Attributes:
- `id` (str): Unique identifier for the node.
- `type` (NodeType): The type of node (agent, router, decision).

#### Methods:
- `execute(self, context: Any) -> Any`
  - **Description**: Executes the logic associated with the node.
- `validate(self) -> bool`
  - **Description**: Validates whether the node is correctly configured.

### BaseEdge (Abstract Base Class)
Represents a connection between two nodes in the graph.

#### Attributes:
- `from_node` (str): The ID of the starting node.
- `to_node` (str): The ID of the destination node.

#### Methods:
- `validate(self) -> bool`
  - **Description**: Ensures the edge is correctly configured.

### GraphProtocol (Protocol)
Defines the expected interface for graph implementations.

#### Methods:
- `add_node(self, node: NodeT) -> None`
- `add_edge(self, edge: EdgeT) -> None`
- `validate(self) -> bool`
- `execute(self, context: ContextT) -> ResultT`

### BaseGraph (Abstract Base Class)
A generic implementation of a directed graph that enforces structure and execution logic.

#### Attributes:
- `nodes` (Dict[str, NodeT]): Maps node IDs to node objects.
- `edges` (Dict[str, List[str]]): Maps node IDs to lists of connected nodes.
- `entry_points` (Set[str]): Nodes where execution begins.
- `exit_points` (Set[str]): Nodes representing termination points.

#### Methods:
- `_validate_node(self, node: NodeT) -> bool`
  - **Description**: Validates a given node.
- `_validate_edge(self, from_node: str, to_node: str) -> bool`
  - **Description**: Validates an edge between two nodes.
- `_execute_node(self, node_id: str, context: ContextT) -> ResultT`
  - **Description**: Executes a specific node within the graph.
- `validate(self) -> bool`
  - **Description**: Validates the overall graph structure.
- `execute(self, context: ContextT) -> Dict[str, ResultT]`
  - **Description**: Executes the graph from its entry points.
- `add_node(self, node: NodeT) -> None`
  - **Description**: Adds a node to the graph.
- `add_edge(self, edge: EdgeT) -> None`
  - **Description**: Adds an edge to the graph.
- `from_dict(cls, data: dict) -> 'BaseGraph'`
  - **Description**: Constructs a graph from a dictionary representation.
- `from_json(cls, json_path: str) -> 'BaseGraph'`
  - **Description**: Constructs a graph from a JSON file.
- `to_dict(self) -> dict`
  - **Description**: Serializes the graph into a dictionary.
- `to_json(self, json_path: str) -> None`
  - **Description**: Saves the graph as a JSON file.

"""

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
    """Enumeration of node types in the graph."""
    AGENT = "agent"
    ROUTER = "router"
    DECISION = "decision"


class BaseNode(BaseModel, ABC):
    """
    Abstract base class for graph nodes, defining the minimal required attributes and behaviors.

    Attributes:
        id (str): A unique identifier for the node.
        type (NodeType): Specifies whether the node is an agent, router, or decision node.
    """

    id: str
    type: NodeType

    @abstractmethod
    def execute(self, context: Any) -> Any:
        """
        Executes the node's logic based on the provided context.

        Args:
            context (Any): The execution context containing relevant input data.

        Returns:
            Any: The result of executing the node.
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """
        Checks whether the node's configuration is valid.

        Returns:
            bool: True if valid, otherwise False.
        """
        pass


class BaseEdge(BaseModel, ABC):
    """
    Abstract base class for edges, defining the structure for connections between nodes.

    Attributes:
        from_node (str): The ID of the originating node.
        to_node (str): The ID of the destination node.
    """

    from_node: str
    to_node: str

    @abstractmethod
    def validate(self) -> bool:
        """
        Ensures the edge configuration is valid.

        Returns:
            bool: True if valid, otherwise False.
        """
        pass


@runtime_checkable
class GraphProtocol(Protocol[NodeT, EdgeT, ContextT, ResultT]):
    """
    Protocol defining the interface that any graph implementation must follow.
    """

    def add_node(self, node: NodeT) -> None:
        """Adds a node to the graph."""
        ...

    def add_edge(self, edge: EdgeT) -> None:
        """Adds an edge to the graph."""
        ...

    def validate(self) -> bool:
        """Validates the graph's structure."""
        ...

    def execute(self, context: ContextT) -> ResultT:
        """Executes the graph using the provided context."""
        ...


class BaseGraph(BaseModel, ABC, Generic[NodeT, EdgeT, ContextT, ResultT]):
    """
    Base class for implementing a directed graph with execution and validation logic.

    Attributes:
        nodes (Dict[str, NodeT]): Dictionary of node ID to node object.
        edges (Dict[str, List[str]]): Dictionary mapping node IDs to their outgoing connections.
        entry_points (Set[str]): Nodes where execution starts.
        exit_points (Set[str]): Nodes where execution terminates.
    """

    nodes: Dict[str, NodeT] = {}
    edges: Dict[str, List[str]] = {}
    entry_points: Set[str] = set()
    exit_points: Set[str] = set()

    @abstractmethod
    def _validate_node(self, node: NodeT) -> bool:
        """Validates an individual node."""
        pass

    @abstractmethod
    def _validate_edge(self, from_node: str, to_node: str) -> bool:
        """Validates the relationship between two nodes."""
        pass

    @abstractmethod
    def _execute_node(self, node_id: str, context: ContextT) -> ResultT:
        """Executes a specific node."""
        pass

    def validate(self) -> bool:
        """
        Validates the overall graph structure, ensuring all nodes and edges are valid.

        Returns:
            bool: True if the graph is valid, otherwise False.
        """
        logger.info("Validating graph structure")
        graph = nx.DiGraph()
        for node_id in self.nodes:
            graph.add_node(node_id)

        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                if not self._validate_edge(from_node, to_node):
                    return False
                graph.add_edge(from_node, to_node)

        for node in self.nodes.values():
            if not self._validate_node(node):
                return False

        reachable = set()
        for entry in self.entry_points:
            reachable.update(nx.descendants(graph, entry))
            reachable.add(entry)

        if not all(node in reachable for node in self.nodes):
            logger.error("Found unreachable nodes in graph")
            return False

        return True

    def execute(self, context: ContextT) -> Dict[str, ResultT]:
        """
        Executes the graph from entry points.

        Returns:
            Dict[str, ResultT]: A dictionary mapping node IDs to execution results.
        """
        if not self.validate():
            raise ValueError("Invalid graph structure")
