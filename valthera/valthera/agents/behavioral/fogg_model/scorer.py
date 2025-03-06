from valthera.models import ValtheraScores, UserContext, Behavior
from typing import Callable, Dict, Any, List, Optional
from collections import defaultdict


def default_transform(value: float, rule: Dict[str, Any]) -> float:
    """
    Default transform function:
    - Scales the value to a 0-1 range based on the rule's "low" and "high" values.
    """
    low = rule.get("low", 0)
    high = rule.get("high", 10)
    if high == low:
        return 1.0  # avoid division by zero; consider value as maximum by default
    # Cap value between low and high then normalize
    capped = max(low, min(value, high))
    return (capped - low) / (high - low)


class ValtheraScorer:
    """
    A flexible scoring system that works off a single list of scoring rules.
    Each rule should have a "type" (e.g., "motivation", "ability", "trigger"),
    a "key", a "weight", and optionally "low", "high", and a "transform"
    function.
    """

    def __init__(self, scoring_rules: List[Dict[str, Any]]):
        """
        scoring_rules: A list of rules defining scoring logic.
        """
        self.scoring_rules = scoring_rules
        self.rules_by_type = self._group_rules_by_type(scoring_rules)

    def _group_rules_by_type(self, rules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped = defaultdict(list)
        for rule in rules:
            rule_type = rule.get("type", "default")
            grouped[rule_type].append(rule)
        return grouped

    def score(self, user_context: UserContext, behavior: Optional[Behavior] = None) -> ValtheraScores:
        motivation = self._calculate_group_score("motivation", user_context, behavior)
        ability = self._calculate_group_score("ability", user_context, behavior)
        trigger = self._calculate_group_score("trigger", user_context, behavior)
        
        # Update the return type as needed. If ValtheraScores does not support a trigger field,
        # then you can omit it or extend the model.
        return ValtheraScores(motivation=motivation, ability=ability, trigger=trigger)

    def _calculate_group_score(
        self, 
        rule_type: str, 
        user_context: UserContext, 
        behavior: Optional[Behavior] = None
    ) -> float:
        """
        Calculate the aggregated score for a given group of rules.
        """
        rules = self.rules_by_type.get(rule_type, [])
        total_score = 0.0
        data = user_context.connector_data

        for rule in rules:
            key = rule["key"]
            weight = rule["weight"]

            # If this is a behavior-specific rule (e.g., behavior_complexity) and a behavior object is provided:
            if key == "behavior_complexity" and behavior is not None:
                value = getattr(behavior, "complexity", 2)  # default complexity is 2 if not defined
            else:
                value = data.get(key, 0)

            # Check if a custom transform is provided; if not, use the default transform.
            transform: Optional[Callable[[float], float]] = rule.get("transform")
            if transform is None:
                factor = default_transform(value, rule)
            else:
                factor = transform(value)

            total_score += weight * factor

        # Ensure the final score is capped between 0 and 1.
        return max(0.0, min(total_score, 1.0))
