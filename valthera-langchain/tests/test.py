import json
import logging
from typing import Dict, Any
from valthera.core.graph import BaseEdge
from valthera_langchain.nodes import LangChainNode
from valthera_langchain.graph import LangChainGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample JSON to define a LangChainGraph with nodes and edges
graph_json = {
    "nodes": [
        {"id": "node1", "type": "agent", "chain_type": "LLMChain", "model_name": "gpt-4"},
        {"id": "node2", "type": "router", "chain_type": "SequentialChain", "model_name": "gpt-4"},
        {"id": "node3", "type": "decision", "chain_type": "ConditionalChain", "model_name": "gpt-4"}
    ],
    "edges": [
        {"from_node": "node1", "to_node": "node2"},
        {"from_node": "node2", "to_node": "node3"}
    ],
    "entry_points": ["node1"],
    "exit_points": ["node3"]
}


def setup_graph_from_json(graph_data: Dict[str, Any]) -> LangChainGraph:
    """Setup a LangChainGraph from JSON data."""
    logger.info("Initializing LangChainGraph from JSON")
    graph = LangChainGraph()
    
    # Add nodes
    for node_data in graph_data["nodes"]:
        node = LangChainNode(**node_data)
        graph.add_node(node)
        
    # Add edges
    class EdgeImplementation(BaseEdge):
        def validate(self) -> bool:
            return True
    
    for edge_data in graph_data["edges"]:
        edge = EdgeImplementation(**edge_data)
        graph.add_edge(edge)
    
    # Define entry and exit points
    graph.entry_points = set(graph_data["entry_points"])
    graph.exit_points = set(graph_data["exit_points"])
    
    return graph


def test_graph_execution():
    """Test execution of LangChainGraph."""
    logger.info("Running test for LangChainGraph execution")
    
    graph = setup_graph_from_json(graph_json)
    
    if not graph.validate():
        logger.error("Graph validation failed")
        return
    
    # Mock execution context
    context = {"input": "What is the weather today?"}
    results = graph.execute(context)
    
    logger.info(f"Graph Execution Results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    test_graph_execution()
