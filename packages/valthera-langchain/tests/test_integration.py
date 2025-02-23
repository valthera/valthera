import pytest
from valthera_langchain.graph import LangChainGraph
from valthera_langchain.nodes import ProcessingNode, FinalNode
import asyncio

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """Test a complete workflow with multiple nodes and state transitions."""
    graph = LangChainGraph()
    
    # Create nodes
    processor = ProcessingNode(chain_type="processor", model_name="test")
    finalizer = FinalNode(chain_type="finalizer", model_name="test")
    
    # Build graph
    graph.add_node("processor", processor)
    graph.add_node("finalizer", finalizer)
    graph.set_entrypoint("processor")
    graph.add_edge("processor", "finalizer")
    
    # Execute
    initial_state = {"input": "test data"}
    result = await graph.execute(initial_state)
    
    # Verify flow
    assert result["processed"]
    assert result["completed"]
    assert "input" in result

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the workflow."""
    graph = LangChainGraph()
    
    class ErrorNode(ProcessingNode):
        """Node that raises an error for testing error handling."""
        def __init__(self, **kwargs):
            super().__init__(chain_type="error", **kwargs)
            
        async def invoke(self, state):
            raise ValueError("Test error")
    
    error_node = ErrorNode(id="error")
    graph.add_node("error", error_node)
    graph.set_entrypoint("error")
    
    with pytest.raises(ValueError, match="Test error"):
        await graph.execute({"input": "test"})

@pytest.mark.integration
@pytest.mark.asyncio
async def test_parallel_execution():
    """Test executing multiple workflows in parallel."""
    async def run_workflow():
        graph = LangChainGraph()
        # Create processor with required configuration
        processor = ProcessingNode(
            id="processor",
            chain_type="parallel_processor",
            model_name="test"
        )
        graph.add_node("processor", processor)
        graph.set_entrypoint("processor")
        return await graph.execute({"input": "test"})
    
    # Run multiple workflows concurrently
    results = await asyncio.gather(
        run_workflow(),
        run_workflow(),
        run_workflow()
    )
    
    assert len(results) == 3
    assert all(r["processed"] for r in results)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_state_propagation():
    """Test that state is properly propagated through the workflow."""
    graph = LangChainGraph()
    
    class StateCheckNode(ProcessingNode):
        """Node that checks and modifies state."""
        def __init__(self, **kwargs):
            super().__init__(chain_type="state_check", **kwargs)
            
        async def invoke(self, state):
            state["checked"] = True
            return state
    
    # Create and configure nodes
    node_a = StateCheckNode(id="node_a")
    node_b = StateCheckNode(id="node_b")
    
    # Build graph
    graph.add_node("a", node_a)
    graph.add_node("b", node_b)
    graph.set_entrypoint("a")
    graph.add_edge("a", "b")
    
    # Execute and verify
    result = await graph.execute({"initial": True})
    assert result["initial"]
    assert result["checked"]