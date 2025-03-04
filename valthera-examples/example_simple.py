import os

from valthera.agent import ValtheraAgent
from valthera.aggregator import DataAggregator
from valthera.scorer import ValtheraScorer
from valthera.reasoning_engine import ReasoningEngine
from valthera.trigger_generator import TriggerGenerator
from valthera.models import User, Behavior
from mocks import hubspot, posthog, snowflake
from langchain_community.chat_models import ChatOpenAI


user = User(
    user_id="user_12345",
    email="sam@example.com"
)

behavior = Behavior(
    behavior_id="behavior_onboarding_1",
    name="Finish Onboarding",
    description="Complete any remaining onboarding steps."
)

data_aggregator = DataAggregator(
    connectors={
        "hubspot": hubspot(),
        "posthog": posthog(),
        "app_db": snowflake()
    }
)

decision_rules = [
            {"condition": "motivation >= 0.75 and ability >= 0.75", "action": "trigger", "description": "moderate ability is acceptable"},
            {"condition": "motivation < 0.75", "action": "improve_motivation", "description": "increase motivation"},
            {"condition": "ability < 0.75", "action": "improve_ability", "description": "increase ability"},
            {"condition": "otherwise", "action": "defer", "description": "not ready yet"},
        ]

reasoning_engine = ReasoningEngine(
    llm=ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.0,  # 0 temperature for consistent reasoning output
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    ),
    decision_rules=decision_rules
    
)


trigger_generator = TriggerGenerator(
    llm=ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,  # Slightly higher for creative messaging
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )    
)


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


agent = ValtheraAgent(
    data_aggregator=data_aggregator,
    bmat_scorer=scorer,
    reasoning_engine=reasoning_engine,
    trigger_generator=trigger_generator
)


recommendation = agent.run(user, behavior, prompt="The messaging should be in the tone of Micky Mouse")


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
