import os
import json
from unittest.mock import MagicMock

from langchain_valthera.tools import ValtheraTool, ValtheraToolInput
from valthera.reasoning_engine import ReasoningEngine
from valthera.trigger_generator import TriggerGenerator
from valthera.aggregator import DataAggregator
from valthera.models import UserContext


# Create a mock LLM response object
class MockMessage:
    def __init__(self, content):
        self.content = content

class MockGeneration:
    def __init__(self, message):
        self.message = message

class MockLLMResult:
    def __init__(self, generations):
        self.generations = generations


# Mock ChatOpenAI to avoid real API calls, with proper _generate method
class MockChatOpenAI:
    def __init__(self, model_name, temperature, openai_api_key):
        self.model_name = model_name
        self.temperature = temperature
        self.openai_api_key = openai_api_key

    def __call__(self, *args, **kwargs):
        return self

    def predict(self, input_text):
        return f"Mock response for input: {input_text}"
    
    def _generate(self, messages, **kwargs):
        # Return a fixed JSON response that follows the expected structure
        content = json.dumps({
            "action": "trigger", 
            "analysis": "Mock analysis: The user has sufficient motivation and ability."
        })
        message = MockMessage(content)
        generation = MockGeneration(message)
        return MockLLMResult([generation])


# Define Motivation & Ability Configurations
motivation_config = [
    {"key": "lead_score", "weight": 0.30, "transform": lambda x: min(int(x), 100) / 100.0},
    {"key": "events_count_past_30days", "weight": 0.30, "transform": lambda x: min(int(x), 50) / 50.0},
    {"key": "marketing_emails_opened", "weight": 0.20, "transform": lambda x: min(int(x) / 10.0, 1.0)},
    {"key": "session_count", "weight": 0.20, "transform": lambda x: min(int(x) / 5.0, 1.0)}
]

ability_config = [
    {"key": "onboarding_steps_completed", "weight": 0.30, "transform": lambda x: min(int(x) / 5.0, 1.0)},
    {"key": "session_count", "weight": 0.30, "transform": lambda x: min(int(x) / 10.0, 1.0)},
    {"key": "behavior_complexity", "weight": 0.40, "transform": lambda x: 1 - (min(int(x), 5) / 5.0)}
]

# Use the mock ChatOpenAI instead of real API calls
mock_reasoning_engine = ReasoningEngine(
    llm=MockChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.0,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)

# Do the same for TriggerGenerator if it uses the _generate method
mock_trigger_generator = TriggerGenerator(
    llm=MockChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)

# Create a mock UserContext
mock_user_context = UserContext(
    user_id="user_12345",
    connector_data={
        "lead_score": 80,
        "events_count_past_30days": 20,
        "marketing_emails_opened": 5,
        "session_count": 3,
        "onboarding_steps_completed": 2,
        "behavior_complexity": 2,
    }
)

# Mock the DataAggregator to return our mock UserContext
mock_data_aggregator = MagicMock(spec=DataAggregator)
mock_data_aggregator.build_user_context.return_value = mock_user_context

# Initialize ValtheraTool with the corrected mock
valthera_tool = ValtheraTool(
    motivation_config=motivation_config,
    ability_config=ability_config,
    reasoning_engine=mock_reasoning_engine,
    trigger_generator=mock_trigger_generator,
    data_aggregator=mock_data_aggregator
)

# Test input
test_input = ValtheraToolInput(
    user_id="user_12345",
    email="sam@example.com",
    behavior_id="behavior_onboarding_1",
    behavior_name="Finish Onboarding",
    behavior_description="Complete any remaining onboarding steps."
)

# Run tool
result = valthera_tool._run(
    user_id=test_input.user_id,
    email=test_input.email,
    behavior_id=test_input.behavior_id,
    behavior_name=test_input.behavior_name,
    behavior_description=test_input.behavior_description
)

# Print output
print("=== Valthera Tool Output ===")
print(result)