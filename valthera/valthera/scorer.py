from valthera.models import ValtheraScores, UserContext, Behavior
from typing import Callable, Dict, Any, List


class ValtheraScorer:
    """
    A flexible scoring system where users define the keys and how to score them.
    """

    def __init__(self, motivation_config: List[Dict[str, Any]], ability_config: List[Dict[str, Any]]):
        """
        - motivation_config: List of scoring rules for motivation.
        - ability_config: List of scoring rules for ability.
        """
        self.motivation_config = motivation_config
        self.ability_config = ability_config

    def score(self, user_context: UserContext, behavior: Behavior) -> ValtheraScores:
        motivation = self._calculate_score(user_context, self.motivation_config)
        ability = self._calculate_score(user_context, self.ability_config, behavior)
        return ValtheraScores(motivation=motivation, ability=ability)

    def _calculate_score(self, user_context: UserContext, config: List[Dict[str, Any]], behavior: Behavior = None) -> float:
        """
        Generic score calculation based on a provided config.
        - user_context: User data from connectors.
        - config: Scoring rules defined by the user.
        - behavior: Optional behavior object (used for ability scoring).
        """
        data = user_context.connector_data
        total_score = 0.0

        for rule in config:
            key = rule["key"]
            weight = rule["weight"]
            transform = rule.get("transform", lambda x: x)  # Default to identity function

            # Special handling for behavior-specific keys
            if key == "behavior_complexity" and behavior:
                value = getattr(behavior, "complexity", 2)  # Default complexity is 2
            else:
                value = data.get(key, 0)

            # Apply transformation (e.g., scaling, capping)
            factor = transform(value)
            total_score += weight * factor

        return max(0.0, min(total_score, 1.0))  # Ensure score is between 0 and 1
