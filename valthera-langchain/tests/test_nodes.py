import pytest
from typing import Dict, Any
from valthera_langchain.nodes import LangChainNode, ProcessingNode, FinalNode

async def test_base_langchain_node():
    node = LangChainNode(chain_type="test", model_name="test-model")
    state = {"input": "test data"}
    result = await node.invoke(state)
    assert result == state
    assert node.chain_type == "test"
    assert node.model_name == "test-model"

async def test_processing_node():
    node = ProcessingNode(chain_type="processor", model_name="test-model")
    state = {"input": "test data"}
    result = await node.invoke(state)
    assert result["processed"] is True
    assert "input" in result

async def test_final_node():
    node = FinalNode(chain_type="finalizer", model_name="test-model")
    state = {"input": "test data", "processed": True}
    result = await node.invoke(state)
    assert result["completed"] is True
    assert "processed" in result

@pytest.mark.asyncio
async def test_node_call_method():
    node = LangChainNode()
    state = {"test": "data"}
    result = await node(state)
    assert result == state

@pytest.fixture
def mock_chain_response():
    return {"response": "test response"}

@pytest.mark.asyncio
async def test_node_with_chain(mock_chain_response):
    class TestNode(LangChainNode):
        async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
            state.update(mock_chain_response)
            return state

    node = TestNode(chain_type="test")
    result = await node({"input": "test"})
    assert result["response"] == mock_chain_response["response"]
