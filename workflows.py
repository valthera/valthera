from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from langchain.agents import BaseSingleActionAgent
from langchain.chat_models.base import BaseChatModel
from valthera.valthera.core.graph import Graph, GraphNode, NodeType

@dataclass
class SupervisorConfig:
    output_mode: str = "full_history"
    memory_type: str = "none"

def create_supervisor(
    agents: List[BaseSingleActionAgent],
    model: BaseChatModel,
    prompt: str,
    config: Optional[SupervisorConfig] = None
) -> Graph:
    """Create a supervisor graph to orchestrate multiple agents."""
    if config is None:
        config = SupervisorConfig()

    # Create router node
    router = GraphNode(
        id="supervisor_router",
        type=NodeType.ROUTER
    )
    
    # Create graph
    graph = Graph()
    graph.add_node(router)
    
    # Add agent nodes
    for agent in agents:
        node = GraphNode(
            id=f"agent_{agent.name}",
            type=NodeType.AGENT,
            agent_id=agent.name
        )
        graph.add_node(node)
        graph.add_edge("supervisor_router", node.id)
        graph.add_edge(node.id, "supervisor_router")  # Enable cycling back
        
    graph.set_entry_point("supervisor_router")
    
    return graph

def add_memory(
    workflow: StateGraph, 
    checkpointer=None,
    store=None
):
    """Add memory capabilities to workflow"""
    return workflow.compile(
        checkpointer=checkpointer,
        store=store
    )
