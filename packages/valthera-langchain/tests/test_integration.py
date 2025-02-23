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
        async def invoke(self, state):
            raise ValueError("Test error")
    
    graph.add_node("error", ErrorNode())
    graph.set_entrypoint("error")
    
    with pytest.raises(ValueError, match="Test error"):
        await graph.execute({"input": "test"})

@pytest.mark.integration
@pytest.mark.asyncio
async def test_parallel_execution():
    """Test executing multiple workflows in parallel."""
    async def run_workflow():
        graph = LangChainGraph()
        processor = ProcessingNode()
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
