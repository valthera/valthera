import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from valthera.agents.behavioral.fogg_model.scorer import ValtheraScorer
from valthera.models import User, Behavior, UserContext
# Removed TriggerDecisionAgent import because it should be used internally by ValtheraTool
from langchain_valthera.tools import ValtheraTool

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

scorer = ValtheraScorer(behavior_weights)

# Use ValtheraTool (which implements BaseTool) rather than TriggerDecisionAgent directly.
valthera_tool = ValtheraTool()

print("✅ ValtheraTool successfully initialized!")

llm = ChatOpenAI(
    model_name="gpt-4-turbo", 
    temperature=0.0, 
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)
tools = [valthera_tool]
graph = create_react_agent(llm, tools=tools)

if __name__ == "__main__":
    inputs = {
        "messages": [("user", "Evaluate behavior for user_12345: Finish Onboarding")]
    }

    print("=== Running LangGraph Agent ===")
    
    for response in graph.stream(inputs, stream_mode="values"):
        print(response)
