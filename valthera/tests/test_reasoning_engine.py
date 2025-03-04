import unittest
from unittest.mock import Mock
from valthera.models import Behavior, ValtheraScores, UserContext
from valthera.reasoning_engine import ReasoningEngine


class TestReasoningEngine(unittest.TestCase):
    def setUp(self):
        self.mock_llm = Mock()
        self.mock_llm._generate.return_value.generations = [Mock(message=Mock(content='{"action": "trigger", "analysis": "Test decision"}'))]
        self.engine = ReasoningEngine(self.mock_llm)

    def test_decide_trigger(self):
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        scores = ValtheraScores(motivation=0.9, ability=0.9)
        decision = self.engine.decide(user_context, behavior, scores)
        self.assertEqual(decision["action"], "trigger")

    def test_decide_improve_motivation(self):
        self.mock_llm._generate.return_value.generations = [Mock(message=Mock(content='{"action": "improve_motivation", "analysis": "Test decision"}'))]
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        scores = ValtheraScores(motivation=0.5, ability=0.9)
        decision = self.engine.decide(user_context, behavior, scores)
        self.assertEqual(decision["action"], "improve_motivation")


if __name__ == "__main__":
    unittest.main()
