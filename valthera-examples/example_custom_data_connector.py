from valthera.aggregator import DataAggregator
from valthera.connectors.base import BaseConnector
from valthera.models import User, UserContext
from valthera.agent import ValtheraAgent
from valthera.aggregator import DataAggregator
from valthera.scorer import ValtheraScorer
from valthera.reasoning_engine import ReasoningEngine
from valthera.trigger_generator import TriggerGenerator
from valthera.models import User, Behavior
from mocks import hubspot, posthog, snowflake
from langchain_community.chat_models import ChatOpenAI
from typing import Dict
import os



class CustomDataSource(BaseConnector):
    """    
    """
    def get_user_data(self, user_id: str):
        return {
            "hubspot_contact_id": "999-ZZZ",
            "lifecycle_stage": "opportunity",
            "lead_status": "engaged",
            "lead_score": 100,  # 100 -> lead_score_factor = 1.0
            "company_name": "MaxMotivation Corp.",
            "last_contacted_date": "2023-09-20",
            "marketing_emails_opened": 20,
            "marketing_emails_clicked": 10,
            "distinct_ids": [user_id, f"email_{user_id}"],
            "last_event_timestamp": "2023-09-20T12:34:56Z",
            "feature_flags": ["beta_dashboard", "early_access"],
            "session_count": 30,                  # e.g. min(session_count/5, 1.0) => 30/5=6 => saturates at 1.0
            "avg_session_duration_sec": 400,
            "recent_event_types": ["pageview", "button_click", "premium_feature_used"],
            "events_count_past_30days": 80,       # min(80, 50)=50 => usage_factor=1.0 in your code
            "onboarding_steps_completed": 5,       # Or 5 if you want high ability too
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "subscription_status": "paid",
            "plan_tier": "premium",
            "account_creation_date": "2023-01-01",
            "preferred_language": "en",
            "last_login_datetime": "2023-09-20T12:00:00Z"
        }


data_aggregator = DataAggregator(
    connectors={
        "custom": CustomDataSource(),        
    }
)

# ------------------------------------------------------------------------------
# Setup: Define the user and behavior you want to influence
# ------------------------------------------------------------------------------
user = User(
    user_id="user_12345",
    email="sam@example.com"
)

behavior = Behavior(
    behavior_id="behavior_onboarding_1",
    name="Finish Onboarding",
    description="Complete any remaining onboarding steps."
)



# ------------------------------------------------------------------------------
# Reasoning Engine: Assess the user's ability and motivation.
#
# This example uses OpenAI's GPT-3.5 for generating reasoning.
# In production, you might replace this with a custom model.
# ------------------------------------------------------------------------------
reasoning_engine = ReasoningEngine(
    llm=ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.0,  # 0 temperature for consistent reasoning output
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)

# ------------------------------------------------------------------------------
# Trigger Generator: Create a trigger message based on the reasoning.
#
# Uses GPT-3.5 to generate a creative trigger message.
# ------------------------------------------------------------------------------
trigger_generator = TriggerGenerator(
    llm=ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,  # Slightly higher for creative messaging
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)

# ------------------------------------------------------------------------------
# Scoring: Evaluate user's readiness (ability & motivation)
#
# This custom scorer uses data from the data aggregator.
# ------------------------------------------------------------------------------

motivation_config = [
    {"key": "hubspot_lead_score", "weight": 0.30, "transform": lambda x: min(x, 100) / 100.0},
    {"key": "posthog_events_count_past_30days", "weight": 0.30, "transform": lambda x: min(x, 50) / 50.0},
    {"key": "hubspot_marketing_emails_opened", "weight": 0.20, "transform": lambda x: min(x / 10.0, 1.0)},
    {"key": "posthog_session_count", "weight": 0.20, "transform": lambda x: min(x / 5.0, 1.0)}
]

ability_config = [
    {"key": "posthog_onboarding_steps_completed", "weight": 0.30, "transform": lambda x: min(x / 5.0, 1.0)},
    {"key": "posthog_session_count", "weight": 0.30, "transform": lambda x: min(x / 10.0, 1.0)},
    {"key": "behavior_complexity", "weight": 0.40, "transform": lambda x: 1 - (min(x, 5) / 5.0)}
]



scorer = ValtheraScorer(motivation_config, ability_config)


# ------------------------------------------------------------------------------
# Agent: Orchestrates the pipeline
#
# The agent brings together the data aggregator, scorer, reasoning engine,
# and trigger generator to decide whether to trigger the user.
# ------------------------------------------------------------------------------
agent = ValtheraAgent(
    data_aggregator=data_aggregator,
    bmat_scorer=scorer,
    reasoning_engine=reasoning_engine,
    trigger_generator=trigger_generator
)

# ------------------------------------------------------------------------------
# Run the pipeline for the defined user and behavior
# ------------------------------------------------------------------------------
recommendation = agent.run(user, behavior)

# ------------------------------------------------------------------------------
# Display the trigger recommendation
# ------------------------------------------------------------------------------
print("=== Valthera Agent Output ===")
if recommendation:
    print("Recommended Trigger:")
    print(f"Message: {recommendation.trigger_message}")
    if recommendation.channel:
        print(f"Channel: {recommendation.channel}")
    if hasattr(recommendation, 'confidence'):
        print(f"Confidence: {recommendation.confidence}")
else:
    print("No trigger recommended (suggested action might be to improve motivation or ability).")
