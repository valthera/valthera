import pytest
from valthera_langchain.graph import LangChainGraph
from valthera_langchain.nodes.base import LangChainNode
from valthera_langchain.nodes import ProcessingNode, FinalNode

@pytest.fixture
def basic_graph():
    return LangChainGraph()

@pytest.fixture
def populated_graph():
    graph = LangChainGraph()
    processor = ProcessingNode(id="processor", chain_type="processor")
    finalizer = FinalNode(id="finalizer", chain_type="finalizer")
    
    graph.add_node("processor", processor)
    graph.add_node("finalizer", finalizer)
    graph.set_entrypoint("processor")
    graph.add_edge("processor", "finalizer")
    
    return graph

def test_graph_initialization(basic_graph):
    assert len(basic_graph.nodes) == 0
    assert not basic_graph.entrypoint_set

def test_add_node(basic_graph):
    node = ProcessingNode(id="test", chain_type="test_processor")
    basic_graph.add_node("test", node)
    assert "test" in basic_graph.nodes
    assert basic_graph.nodes["test"] == node

def test_set_entrypoint(populated_graph):
    assert populated_graph.entrypoint_set
    with pytest.raises(ValueError):
        populated_graph.set_entrypoint("nonexistent")

def test_add_edge(populated_graph):
    assert populated_graph._validate_edge("processor", "finalizer")
    assert not populated_graph._validate_edge("nonexistent", "finalizer")

def test_validate_edge(populated_graph):
    assert populated_graph._validate_edge("processor", "finalizer")
    assert not populated_graph._validate_edge("invalid", "node")

@pytest.mark.asyncio
async def test_graph_execution(populated_graph):
    initial_state = {"input": "test"}
    result = await populated_graph.execute(initial_state)
    assert result["processed"]
    assert result["completed"]

@pytest.mark.asyncio
async def test_graph_compilation_without_entrypoint(basic_graph):
    with pytest.raises(ValueError, match="No entrypoint set for the graph"):
        basic_graph.compile()

@pytest.mark.asyncio
async def test_complex_graph_flow():
    graph = LangChainGraph()
    
    class NodeA(LangChainNode):
        async def invoke(self, state):
            state["a"] = True
            return state
            
    class NodeB(LangChainNode):
        async def invoke(self, state):
            state["b"] = True
            return state
    
    node_a = NodeA(id="a", chain_type="node_a")
    node_b = NodeB(id="b", chain_type="node_b")
    
    graph.add_node("a", node_a)
    graph.add_node("b", node_b)
    graph.set_entrypoint("a")
    graph.add_edge("a", "b")
    
    result = await graph.execute({"input": "test"})
    assert result["a"]
    assert result["b"]