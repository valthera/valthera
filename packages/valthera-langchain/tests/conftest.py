import pytest
from typing import Dict, Any
from valthera_langchain.nodes import LangChainNode

@pytest.fixture
def mock_state():
    return {"input": "test data"}

@pytest.fixture
def mock_node():
    class MockNode(LangChainNode):
        async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
            state["mock_processed"] = True
            return state
    return MockNode()

@pytest.fixture
def mock_chain_response():
    return {"response": "test response", "metadata": {"confidence": 0.9}}

@pytest.fixture
def error_state():
    return {"error": "test error"}

# Add more fixtures as needed
