import unittest
from unittest.mock import Mock
from valthera.models import UserContext, Behavior, TriggerRecommendation
from valthera.agents.behavioral.fogg_model.trigger_decision_agent.agent import TriggerDecisionAgent

class TestValtheraAgent(unittest.TestCase):
    def setUp(self):
        # Create mocks for the scorer and reasoning engine.
        self.mock_scorer = Mock()
        self.mock_engine = Mock()
        # Use an empty list as a dummy for behavior_weights.
        self.mock_behavior_weights = []
        self.agent = TriggerDecisionAgent(self.mock_behavior_weights)
        # Override the internal scorer and reasoning_engine with our mocks.
        self.agent.scorer = self.mock_scorer
        self.agent.reasoning_engine = self.mock_engine

    def test_run_trigger(self):
        # Create a dummy UserContext with minimal connector_data.
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        dummy_scores = {"dummy": 1}
        # Set up the mocks to simulate a trigger decision.
        self.mock_scorer.score.return_value = dummy_scores
        self.mock_engine.decide.return_value = TriggerRecommendation(trigger_message="Test trigger")
        
        result = self.agent.run(user_context, behavior)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.trigger_message, "Test trigger")

    def test_run_no_trigger(self):
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        dummy_scores = {"dummy": 1}
        self.mock_scorer.score.return_value = dummy_scores
        # Simulate a decision that defers the trigger (i.e. no recommendation).
        self.mock_engine.decide.return_value = None
        
        result = self.agent.run(user_context, behavior)
        
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
