from typing import Optional
from valthera.models import User, Behavior, TriggerRecommendation
from valthera.aggregator import DataAggregator
from valthera.reasoning_engine import ReasoningEngine
from valthera.trigger_generator import TriggerGenerator
from valthera.scorer import ValtheraScorer


class ValtheraAgent:
    """
    High-level orchestrator that runs the pipeline for a given user & behavior.
    """

    def __init__(self,
                 data_aggregator: DataAggregator,
                 bmat_scorer: ValtheraScorer,
                 reasoning_engine: ReasoningEngine,
                 trigger_generator: TriggerGenerator):
        self.data_aggregator = data_aggregator
        self.bmat_scorer = bmat_scorer
        self.reasoning_engine = reasoning_engine
        self.trigger_generator = trigger_generator

    def run(self,
            user: User,
            behavior: Behavior,
            prompt: Optional[str] = "") -> Optional[TriggerRecommendation]:

        user_context = self.data_aggregator.build_user_context(user)
        scores = self.bmat_scorer.score(user_context, behavior)
        decision = self.reasoning_engine.decide(user_context, behavior, scores)

        print(decision)
        if decision["action"] == "trigger":
            trigger = self.trigger_generator.generate_trigger(
                user_context,
                behavior,
                scores,
                prompt
            )
            return trigger
        elif decision["action"] == "improve_motivation":
            # Possibly return a different type of recommendation
            # or store an action plan
            return None
        elif decision["action"] == "improve_ability":
            # Possibly return an action plan for removing friction
            return None
        else:
            # Defer
            print(decision)
            return None
