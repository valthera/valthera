import os
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from typing import Callable, Optional, Dict, List, Any
from valthera.models import UserContext, Behavior, TriggerRecommendation
from valthera.agents.behavioral.fogg_model.scorer import ValtheraScorer
from valthera.agents.behavioral.fogg_model.reasoning_engine import ReasoningEngine


class TriggerDecisionAgent:
    """
    Agent that determines if a trigger should be sent based on the Fogg model.
    """

    def __init__(
            self,            
            behavior_weights: List[Dict[str, Any]],
            model_name: str = 'gpt-4o'
            ) -> None:        
        self.model_name = model_name        
        self.scorer = ValtheraScorer(behavior_weights)
        self.reasoning_engine = ReasoningEngine(
            llm=ChatOpenAI(
                model_name="gpt-4-turbo",
                temperature=0.0,
                openai_api_key=os.environ.get("OPENAI_API_KEY")
            )            
        )

    def run(self,
            user_context: UserContext,
            behavior: Behavior) -> Optional[TriggerRecommendation]:
        scores = self.scorer.score(user_context, behavior)
        decision = self.reasoning_engine.decide(
                user_context,
                behavior,
                scores
            )
        print(decision)
        return decision
