from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel
from enum import Enum
from valthera.core.agent import AgentResponse
from valthera.core.prompt import Prompt
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint
import networkx as nx
import json
import logging

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    AGENT = "agent"
    ROUTER = "router"
    DECISION = "decision"


class GraphNode(BaseModel):
    id: str
    type: NodeType
    agent_id: Optional[str] = None
    action: Optional[str] = None
    condition: Optional[str] = None
    
    def execute(self, context: Dict[str, Any]) -> AgentResponse:
        logger.info(f"Executing node {self.id} of type {self.type}")
        if self.type == NodeType.AGENT:
            logger.debug(f"Executing agent node {self.id} with agent_id {self.agent_id}")
            return self._execute_agent(context)
        elif self.type == NodeType.ROUTER:
            logger.debug(f"Executing router node {self.id}")
            return self._execute_router(context)
        elif self.type == NodeType.DECISION:
            logger.debug(f"Executing decision node {self.id}")
            return self._execute_decision(context)
        
    def _execute_agent(self, context):
        # Agent execution logic
        pass

    def _execute_router(self, context):
        # Router logic for multi-agent workflows
        pass

    def _execute_decision(self, context):
        # Decision node logic
        pass


class Graph(BaseModel):
    nodes: Dict[str, GraphNode] = {}
    edges: Dict[str, List[str]] = {}
    entry_points: Set[str] = set()
    exit_points: Set[str] = set()
    cycles: List[List[str]] = []  # Add this line

    @classmethod
    def from_dict(cls, data: dict) -> 'Graph':
        logger.info("Creating graph from dictionary data")
        graph = cls()
        
        logger.debug(f"Loading {len(data.get('nodes', []))} nodes")
        for node_data in data.get('nodes', []):
            node = GraphNode(
                id=node_data['id'],
                type=NodeType(node_data['type']),
                agent_id=node_data.get('agent_id'),
                action=node_data.get('action'),
                condition=node_data.get('condition')
            )
            graph.add_node(node)
            
        logger.debug(f"Loading {len(data.get('edges', []))} edges")
        for edge in data.get('edges', []):
            graph.add_edge(edge['from'], edge['to'])
            
        logger.debug("Loading entry and exit points")
        for entry in data.get('entry_points', []):
            graph.set_entry_point(entry)
        for exit_point in data.get('exit_points', []):
            graph.set_exit_point(exit_point)
            
        return graph

    @classmethod
    def from_json(cls, json_path: str) -> 'Graph':
        logger.info(f"Loading graph from JSON file: {json_path}")
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load graph from {json_path}: {str(e)}")
            raise
    
    def add_node(self, node: GraphNode):
        logger.debug(f"Adding node {node.id} of type {node.type}")
        self.nodes[node.id] = node
        
    def add_edge(self, from_node: str, to_node: str):
        logger.debug(f"Adding edge from {from_node} to {to_node}")
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        
    def set_entry_point(self, node_id: str):
        if node_id in self.nodes:
            logger.debug(f"Setting {node_id} as entry point")
            self.entry_points.add(node_id)
        else:
            logger.warning(f"Attempted to set non-existent node {node_id} as entry point")
            
    def set_exit_point(self, node_id: str):
        if node_id in self.nodes:
            logger.debug(f"Setting {node_id} as exit point")
            self.exit_points.add(node_id)
        else:
            logger.warning(f"Attempted to set non-existent node {node_id} as exit point")

    def validate(self) -> bool:
        logger.info("Validating graph structure")
        graph = nx.DiGraph()
        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                graph.add_edge(from_node, to_node)
                
        logger.debug("Checking for unreachable nodes")
        reachable = set()
        for entry in self.entry_points:
            reachable.update(nx.descendants(graph, entry))
            reachable.add(entry)
            
        if not all(node in reachable for node in self.nodes):
            logger.error("Found unreachable nodes in graph")
            return False
            
        logger.debug("Detecting cycles in graph")
        self.cycles = list(nx.simple_cycles(graph))
        if self.cycles:
            logger.info(f"Found {len(self.cycles)} cycles in graph")
        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting graph execution")
        if not self.validate():
            logger.error("Graph validation failed")
            raise ValueError("Invalid graph structure")
            
        visited = set()
        results = {}
        
        def execute_node(node_id: str) -> Any:
            if node_id in visited:
                logger.debug(f"Node {node_id} already executed, returning cached result")
                return results[node_id]
                
            logger.info(f"Executing node {node_id}")
            visited.add(node_id)
            node = self.nodes[node_id]
            response = node.execute(context)
            results[node_id] = response
            
            if node_id in self.edges:
                next_nodes = self.edges[node_id]
                logger.debug(f"Node {node_id} has {len(next_nodes)} next nodes")
                for next_node in next_nodes:
                    execute_node(next_node)
                    
            return response
            
        logger.info(f"Starting execution from {len(self.entry_points)} entry points")
        for entry in self.entry_points:
            execute_node(entry)
            
        logger.info("Graph execution completed")
        return results

    def to_json(self, json_path: str):
        logger.info(f"Saving graph to JSON file: {json_path}")
        data = {
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type,
                    'agent_id': node.agent_id,
                    'action': node.action,
                    'condition': node.condition
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {'from': from_node, 'to': to_node}
                for from_node, to_nodes in self.edges.items()
                for to_node in to_nodes
            ],
            'entry_points': list(self.entry_points),
            'exit_points': list(self.exit_points)
        }
        
        try:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Successfully saved graph to JSON")
        except Exception as e:
            logger.error(f"Failed to save graph to {json_path}: {str(e)}")
            raise

    def pretty_print(self):
        """Pretty print the entire graph structure using rich."""
        console = Console()
        
        # Create main tree
        tree = Tree("🔰 Graph Structure")
        
        # Add nodes section
        nodes_tree = tree.add("📍 Nodes")
        for node_id, node in self.nodes.items():
            node_tree = nodes_tree.add(f"[bold blue]{node_id}[/]")
            node_tree.add(f"Type: [cyan]{node.type}[/]")
            if node.agent_id:
                node_tree.add(f"Agent ID: [green]{node.agent_id}[/]")
            if node.action:
                node_tree.add(f"Action: [yellow]{node.action}[/]")
            if node.condition:
                node_tree.add(f"Condition: [magenta]{node.condition}[/]")

        # Add edges section
        edges_tree = tree.add("↔️  Edges")
        for from_node, to_nodes in self.edges.items():
            edge_tree = edges_tree.add(f"[bold blue]{from_node}[/]")
            for to_node in to_nodes:
                edge_tree.add(f"→ [bold cyan]{to_node}[/]")

        # Add entry/exit points
        entry_tree = tree.add("🚪 Entry Points")
        for entry in self.entry_points:
            entry_tree.add(f"[bold green]{entry}[/]")

        exit_tree = tree.add("🏁 Exit Points")
        for exit_point in self.exit_points:
            exit_tree.add(f"[bold red]{exit_point}[/]")

        # Add cycles if any
        if self.cycles:
            cycles_tree = tree.add("🔄 Cycles")
            for i, cycle in enumerate(self.cycles, 1):
                cycle_str = " → ".join(cycle)
                cycles_tree.add(f"Cycle {i}: [yellow]{cycle_str}[/]")

        console.print(tree)

    def print_as_table(self):
        """Print graph information in tabular format."""
        console = Console()

        # Nodes table
        nodes_table = Table(title="Nodes")
        nodes_table.add_column("ID", style="bold blue")
        nodes_table.add_column("Type", style="cyan")
        nodes_table.add_column("Agent ID", style="green")
        nodes_table.add_column("Action", style="yellow")
        nodes_table.add_column("Condition", style="magenta")

        for node_id, node in self.nodes.items():
            nodes_table.add_row(
                node_id,
                str(node.type),
                str(node.agent_id or ""),
                str(node.action or ""),
                str(node.condition or "")
            )

        # Edges table
        edges_table = Table(title="Edges")
        edges_table.add_column("From", style="bold blue")
        edges_table.add_column("To", style="bold cyan")

        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                edges_table.add_row(from_node, to_node)

        console.print("\n[bold]Graph Information[/]")
        console.print(nodes_table)
        console.print(edges_table)
        
        if self.cycles:
            console.print("\n[bold red]Cycles Detected:[/]")
            for i, cycle in enumerate(self.cycles, 1):
                console.print(f"Cycle {i}: [yellow]{' → '.join(cycle)}[/]")

        console.print(f"\n[bold green]Entry Points:[/] {', '.join(self.entry_points)}")
        console.print(f"[bold red]Exit Points:[/] {', '.join(self.exit_points)}")

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize graph from dictionary data
    graph_data = {
        "nodes": [
            {
                "id": "router",
                "type": "router"
            },
            {
                "id": "agent1",
                "type": "agent",
                "agent_id": "agent1"
            },
            {
                "id": "agent2",
                "type": "agent",
                "agent_id": "agent2"
            },
            {
                "id": "agent3",
                "type": "agent",
                "agent_id": "agent3"
            },
            {
                "id": "decision",
                "type": "decision"
            }
        ],
        "edges": [
            {"from": "router", "to": "agent1"},
            {"from": "agent1", "to": "agent2"},
            {"from": "agent1", "to": "agent3"},
            {"from": "agent2", "to": "decision"},
            {"from": "agent3", "to": "agent2"},
            {"from": "decision", "to": "router"}
        ],
        "entry_points": ["router"],
        "exit_points": []
    }
    
    # Create graph from dictionary
    graph = Graph.from_dict(graph_data)
    assert graph.validate()

    # Execute
    context = {"prompt": Prompt(text="Test prompt")}
    results = graph.execute(context)

    # Optionally save to JSON
    graph.to_json("workflow.json")
    
    # Load graph from JSON
    loaded_graph = Graph.from_json("workflow.json")
    assert loaded_graph.validate()

    # Pretty print the graph
    print("\n=== Tree View ===")
    graph.pretty_print()
    
    print("\n=== Table View ===")
    graph.print_as_table()
