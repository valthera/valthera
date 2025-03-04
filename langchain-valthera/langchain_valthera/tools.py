import os
from typing import Type, Optional, List, Dict
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from langchain_openai import ChatOpenAI
from valthera.agent import ValtheraAgent
from valthera.aggregator import DataAggregator
from valthera.scorer import ValtheraScorer
from valthera.reasoning_engine import ReasoningEngine
from valthera.trigger_generator import TriggerGenerator
from valthera.models import User, Behavior
from valthera.connectors.base import BaseConnector


class ValtheraToolInput(BaseModel):
    """Input schema for Valthera tool."""
    user_id: str = Field(..., description="Unique identifier for the user.")
    email: str = Field(..., description="User's email address.")
    behavior_id: str = Field(..., description="ID of the behavior being evaluated.")
    behavior_name: str = Field(..., description="Name of the behavior.")
    behavior_description: str = Field(..., description="Description of the behavior.")


class ValtheraToolConfig(BaseModel):
    """Configuration schema for Valthera tool."""
    motivation_config: List[Dict] = Field(..., description="Scoring configuration for motivation.")
    ability_config: List[Dict] = Field(..., description="Scoring configuration for ability.")


class CustomDataSource(BaseConnector):
    """Mock Data Source for Valthera."""
    
    def get_user_data(self, user_id: str):
        return {
            "hubspot_contact_id": "999-ZZZ",
            "lifecycle_stage": "opportunity",
            "lead_status": "engaged",
            "lead_score": 100,
            "company_name": "MaxMotivation Corp.",
            "marketing_emails_opened": 20,
            "session_count": 30,
            "events_count_past_30days": 80,
            "onboarding_steps_completed": 5,
            "user_id": user_id,
            "email": f"{user_id}@example.com"
        }


class ValtheraTool(BaseTool):
    """LangChain tool for Valthera's behavior-driven AI."""
    
    name: str = "valthera_tool"
    description: str = "Evaluates user readiness for a behavior and generates personalized triggers."
    args_schema: Type[BaseModel] = ValtheraToolInput

    _data_aggregator: DataAggregator = PrivateAttr()
    _scorer: ValtheraScorer = PrivateAttr()
    _reasoning_engine: ReasoningEngine = PrivateAttr()
    _trigger_generator: TriggerGenerator = PrivateAttr()

    def __init__(
        self,
        data_aggregator: DataAggregator,
        motivation_config: List[Dict],
        ability_config: List[Dict],
        reasoning_engine: Optional[ReasoningEngine] = None,
        trigger_generator: Optional[TriggerGenerator] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self._data_aggregator = data_aggregator
    
        self._scorer = ValtheraScorer(motivation_config, ability_config)
                
        self._reasoning_engine = reasoning_engine or ReasoningEngine(
            llm=ChatOpenAI(
                model_name="gpt-4-turbo",
                temperature=0.0,
                openai_api_key=os.environ.get("OPENAI_API_KEY")
            )
        )

        self._trigger_generator = trigger_generator or TriggerGenerator(
            llm=ChatOpenAI(
                model_name="gpt-4-turbo",
                temperature=0.7,
                openai_api_key=os.environ.get("OPENAI_API_KEY")
            )
        )        

    def _run(
        self,
        user_id: str,
        email: str,
        behavior_id: str,
        behavior_name: str,
        behavior_description: str
    ) -> str:
        """Executes the Valthera tool for behavior-driven recommendations."""
        
        user = User(user_id=user_id, email=email)
        behavior = Behavior(
            behavior_id=behavior_id,
            name=behavior_name,
            description=behavior_description
        )

        agent = ValtheraAgent(
            data_aggregator=self._data_aggregator,
            bmat_scorer=self._scorer,
            reasoning_engine=self._reasoning_engine,
            trigger_generator=self._trigger_generator
        )

        recommendation = agent.run(user, behavior)

        if recommendation:
            return f"Trigger Message: {recommendation.trigger_message}, Channel: {recommendation.channel}, Confidence: {recommendation.confidence}"
        return "No trigger recommended (suggested action might be to improve motivation or ability)."


# === 🚀 TESTING THE CONFIGURABLE LANGCHAIN TOOL ===
if __name__ == "__main__":
    motivation_config = [
        {"key": "lead_score", "weight": 0.30, "transform": lambda x: min(x, 100) / 100.0},
        {"key": "events_count_past_30days", "weight": 0.30, "transform": lambda x: min(x, 50) / 50.0},
        {"key": "marketing_emails_opened", "weight": 0.20, "transform": lambda x: min(x / 10.0, 1.0)},
        {"key": "session_count", "weight": 0.20, "transform": lambda x: min(x / 5.0, 1.0)}
    ]

    ability_config = [
        {"key": "onboarding_steps_completed", "weight": 0.30, "transform": lambda x: min(x / 5.0, 1.0)},
        {"key": "session_count", "weight": 0.30, "transform": lambda x: min(x / 10.0, 1.0)},
        {"key": "behavior_complexity", "weight": 0.40, "transform": lambda x: 1 - (min(x, 5) / 5.0)}
    ]

    data_aggregator = DataAggregator(connectors={"custom": CustomDataSource()})

    valthera_tool = ValtheraTool(
        data_aggregator=data_aggregator,
        motivation_config=motivation_config,
        ability_config=ability_config
    )

    # Test input
    test_input = ValtheraToolInput(
        user_id="user_12345",
        email="sam@example.com",
        behavior_id="behavior_onboarding_1",
        behavior_name="Finish Onboarding",
        behavior_description="Complete any remaining onboarding steps."
    )

    # Run tool
    result = valthera_tool._run(
        user_id=test_input.user_id,
        email=test_input.email,
        behavior_id=test_input.behavior_id,
        behavior_name=test_input.behavior_name,
        behavior_description=test_input.behavior_description
    )

    # Print output
    print("=== Valthera Tool Output ===")
    print(result)
