import os
import json
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from valthera.agents.behavioral.fogg_model.scorer import ValtheraScorer
from langchain_valthera.tools import ValtheraTool



# Define behavior weights for the scorer (if used internally)
behavior_weights = [
    {"type": "motivation", "key": "posthog_session_count", "weight": 0.30, "low": 0, "high": 10},
    {"type": "motivation", "key": "posthog_events_count_past_30days", "weight": 0.30, "low": 0, "high": 10},
    {"type": "motivation", "key": "hubspot_marketing_emails_opened", "weight": 0.20, "low": 0, "high": 10},
    {"type": "ability", "key": "posthog_onboarding_steps_completed", "weight": 0.50, "low": 0, "high": 10},
    {"type": "ability", "key": "custom_action", "weight": 0.50, "low": 0, "high": 10}
]

scorer = ValtheraScorer(behavior_weights)

# Initialize the ValtheraTool (which implements BaseTool)
valthera_tool = ValtheraTool()
print("✅ ValtheraTool successfully initialized!")

# Initialize the ChatOpenAI LLM
llm = ChatOpenAI(
    model_name="gpt-4-turbo",
    temperature=0.0,
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

# Create a list of tools including ValtheraTool
tools = [valthera_tool]

# Create the React agent using LangGraph
graph = create_react_agent(llm, tools=tools)

if __name__ == "__main__":
    # Correct JSON structure with separate top-level keys for user_context and behavior
    data = {        
        "connector_data": {
            "hubspot_lead_score": 80,
            "posthog_events_count_past_30days": 40,
            "hubspot_marketing_emails_opened": 8,
            "posthog_session_count": 10,
            "posthog_onboarding_steps_completed": 8,
            "custom_action": 8
        },        
        "behavior": {
            "behavior_id": "complete_onboarding",
            "name": "Complete Onboarding",
            "description": "Complete the onboarding process to get started"
        }
    }

    # Convert the data dict to a JSON string wrapped in a messages list
    inputs = {
        "messages": [("user", json.dumps(data))]
    }

    print("=== Running LangGraph Agent ===")

    # Stream and print responses from the agent
    for response in graph.stream(inputs, stream_mode="values"):
        print(response)
