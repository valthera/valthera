import unittest
from unittest.mock import Mock
from valthera.models import User, Behavior, TriggerRecommendation
from valthera.agents.trigger.agent import ValtheraAgent


class TestValtheraAgent(unittest.TestCase):
    def setUp(self):
        self.mock_aggregator = Mock()
        self.mock_scorer = Mock()
        self.mock_engine = Mock()
        self.mock_generator = Mock()
        self.agent = ValtheraAgent(self.mock_aggregator, self.mock_scorer, self.mock_engine, self.mock_generator)

    def test_run_trigger(self):
        user = User(user_id="123", email="test@example.com")
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        self.mock_engine.decide.return_value = {"action": "trigger"}
        self.mock_generator.generate_trigger.return_value = TriggerRecommendation(trigger_message="Test trigger")
        result = self.agent.run(user, behavior)
        self.assertIsNotNone(result)
        self.assertEqual(result.trigger_message, "Test trigger")

    def test_run_no_trigger(self):
        user = User(user_id="123", email="test@example.com")
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        self.mock_engine.decide.return_value = {"action": "defer"}
        result = self.agent.run(user, behavior)
        self.assertIsNone(result)
