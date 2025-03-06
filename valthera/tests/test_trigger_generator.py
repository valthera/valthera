import unittest
from unittest.mock import Mock
from valthera.models import Behavior, ValtheraScores, UserContext
from valthera.agents.behavioral.fogg_model.trigger_generator import TriggerGenerator

class TestTriggerGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_llm = Mock()
        self.mock_llm._generate.return_value.generations = [
            Mock(message=Mock(content='{"cta": "Try now!", "confidence": 0.8}'))
        ]
        self.generator = TriggerGenerator(self.mock_llm)

    def test_generate_trigger(self):
        user_context = UserContext(user_id="123", connector_data={})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        # Include the 'trigger' field in ValtheraScores.
        scores = ValtheraScores(motivation=0.9, ability=0.9, trigger=0.9)
        trigger = self.generator.generate_trigger(user_context, behavior, scores)
        self.assertEqual(trigger.trigger_message, "Try now!")
        self.assertEqual(trigger.confidence, 0.8)

if __name__ == '__main__':
    unittest.main()
