import os
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from typing import Callable, Optional, Dict, List, Any
from valthera.models import UserContext, Behavior, TriggerRecommendation
from valthera.agents.behavioral.fogg_model.scorer import ValtheraScorer
from valthera.agents.behavioral.fogg_model.reasoning_engine import ReasoningEngine
from valthera.agents.behavioral.fogg_model.trigger_generator import TriggerGenerator


behavior = Behavior(
    behavior_id="complete_onboarding",
    name="Complete Onboarding",
    description="Complete the onboarding process to get started"
)

user_context = UserContext(
    user_id="12345",
    connector_data={
        "hubspot_lead_score": 80,
        "posthog_events_count_past_30days": 40,
        "hubspot_marketing_emails_opened": 8,
        "posthog_session_count": 10,
        "posthog_onboarding_steps_completed": 8,
        "custom_action": 8
    }
)

behavior_weights = [
    {"type": "motivation", "key": "posthog_session_count", "weight": 0.30, "low": 0, "high": 10},
    {"type": "motivation", "key": "posthog_events_count_past_30days", "weight": 0.30, "low": 0, "high": 10},
    {"type": "motivation", "key": "hubspot_marketing_emails_opened", "weight": 0.20, "low": 0, "high": 10},
    {"type": "ability", "key": "posthog_onboarding_steps_completed", "weight": 0.50, "low": 0, "high": 10},
    {"type": "ability", "key": "custom_action", "weight": 0.50, "low": 0, "high": 10}    
]


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
