import unittest
from valthera.models import Behavior, UserContext, ValtheraScores
from valthera.agents.behavioral.fogg_model.scorer import ValtheraScorer

class TestValtheraScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = ValtheraScorer(
            scoring_rules=[
                {
                    "type": "motivation",
                    "key": "engagement",
                    "weight": 1.0,
                    "transform": lambda x: x,
                    "low": 0,
                    "high": 1
                },
                {
                    "type": "ability",
                    "key": "experience",
                    "weight": 1.0,
                    "transform": lambda x: x,
                    "low": 0,
                    "high": 1
                }
            ]
        )

    def test_score_motivation(self):
        user_context = UserContext(user_id="123", connector_data={"engagement": 0.8})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        scores = self.scorer.score(user_context, behavior)
        self.assertEqual(scores.motivation, 0.8)

    def test_score_ability(self):
        user_context = UserContext(user_id="123", connector_data={"experience": 0.9})
        behavior = Behavior(behavior_id="test_behavior", name="Test", description="Test description")
        scores = self.scorer.score(user_context, behavior)
        self.assertEqual(scores.ability, 0.9)

if __name__ == "__main__":
    unittest.main()
