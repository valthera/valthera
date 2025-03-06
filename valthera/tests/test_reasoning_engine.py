import unittest
import json
from unittest.mock import Mock
from valthera.models import Behavior, ValtheraScores, UserContext
from valthera.agents.behavioral.fogg_model.reasoning_engine import ReasoningEngine, HumanMessage, SystemMessage

# Fake classes to simulate a proper LLM response.
class FakeMessage:
    def __init__(self, content: str):
        self.content = content

class FakeGeneration:
    def __init__(self, content: str):
        self.message = FakeMessage(content)

class FakeLLMResponse:
    def __init__(self, content: str):
        self.generations = [FakeGeneration(content)]
    
    # Make the FakeLLMResponse subscriptable.
    def __getitem__(self, index):
        return self.generations[index]

class TestReasoningEngine(unittest.TestCase):
    def setUp(self):
        self.mock_llm = Mock()
        # Set a default fake response for the LLM's _generate method.
        self.mock_llm._generate.return_value = FakeLLMResponse(
            '{"action": "trigger", "analysis": "Test decision"}'
        )
        self.engine = ReasoningEngine(self.mock_llm)

    def test_decide_trigger(self):
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        scores = ValtheraScores(motivation=0.9, ability=0.9, trigger=0.9)
        decision = self.engine.decide(user_context, behavior, scores)
        self.assertIsInstance(decision, dict)
        self.assertEqual(decision["action"], "trigger")

    def test_decide_improve_motivation(self):
        # Update the fake response for this test.
        self.mock_llm._generate.return_value = FakeLLMResponse(
            '{"action": "improve_motivation", "analysis": "Test decision"}'
        )
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        scores = ValtheraScores(motivation=0.5, ability=0.9, trigger=0.9)
        decision = self.engine.decide(user_context, behavior, scores)
        self.assertIsInstance(decision, dict)
        self.assertEqual(decision["action"], "improve_motivation")

if __name__ == "__main__":
    unittest.main()
