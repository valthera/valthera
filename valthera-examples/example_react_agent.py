import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from mocks import hubspot, posthog, snowflake

from valthera.aggregator import DataAggregator
from valthera.scorer import ValtheraScorer
from valthera.reasoning_engine import ReasoningEngine
from valthera.trigger_generator import TriggerGenerator
from valthera.models import User, Behavior
from langchain_valthera.tools import ValtheraTool

# ✅ Initialize Data Aggregator
data_aggregator = DataAggregator(
    connectors={
        "hubspot": hubspot(),
        "posthog": posthog(),
        "app_db": snowflake()
    }
)

# ✅ Motivation and Ability Configurations
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

decision_rules = [
        {"condition": "motivation >= 0.75 and ability >= 0.75", "action": "trigger", "description": "moderate ability is acceptable"},
        {"condition": "motivation < 0.75", "action": "improve_motivation", "description": "increase motivation"},
        {"condition": "ability < 0.75", "action": "improve_ability", "description": "increase ability"},
        {"condition": "otherwise", "action": "defer", "description": "not ready yet"},
    ]

# ✅ Initialize Scorer
scorer = ValtheraScorer(motivation_config, ability_config)

# ✅ Initialize Reasoning Engine
reasoning_engine = ReasoningEngine(
    llm=ChatOpenAI(
        model_name="gpt-4-turbo",
        temperature=0.0,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    ),
    decision_rules=decision_rules
)

# ✅ Initialize Trigger Generator
trigger_generator = TriggerGenerator(
    llm=ChatOpenAI(
        model_name="gpt-4-turbo",
        temperature=0.7,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
)

# ✅ Now instantiate ValtheraTool with required arguments
valthera_tool = ValtheraTool(
    data_aggregator=data_aggregator,
    motivation_config=motivation_config,
    ability_config=ability_config,    
    reasoning_engine=reasoning_engine,
    trigger_generator=trigger_generator
)

print("✅ ValtheraTool successfully initialized!")

# 🔹 Initialize LangGraph React Agent
llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.0, openai_api_key=os.environ.get("OPENAI_API_KEY"))
tools = [valthera_tool]
graph = create_react_agent(llm, tools=tools)

# 🔹 Run LangGraph Agent
if __name__ == "__main__":
    inputs = {
        "messages": [("user", "Evaluate behavior for user_12345: Finish Onboarding")]
    }

    print("=== Running LangGraph Agent ===")
    
    for response in graph.stream(inputs, stream_mode="values"):
        print(response)
