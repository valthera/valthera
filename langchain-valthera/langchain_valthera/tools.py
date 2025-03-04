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


class ValtheraTool(BaseTool):
    """
    LangChain tool for Valthera's behavior-driven AI.

    ValtheraTool evaluates a user's motivation and ability for a given behavior using aggregated data
    (HubSpot, PostHog, Snowflake, etc.), calculates behavior readiness, and generates personalized
    triggers when conditions are met. It helps optimize user engagement by determining the right time
    and message to prompt action.
    """
    
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
                model_name="gpt-4o",
                temperature=0.0,
                openai_api_key=os.environ.get("OPENAI_API_KEY")
            )
        )

        self._trigger_generator = trigger_generator or TriggerGenerator(
            llm=ChatOpenAI(
                model_name="gpt-4o",
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


class CustomDataSource:
    """
    A class for representing custom data sources for Valthera tools.
    
    This class allows users to define and configure custom data sources
    that can be used with Valthera tools for various operations.
    """
    
    def __init__(self, name: str, config: dict = None):
        """
        Initialize a custom data source.
        
        Args:
            name: Name of the custom data source
            config: Configuration dictionary for the data source
        """
        self.name = name
        self.config = config or {}
    
    def get_config(self) -> dict:
        """Return the configuration for this data source"""
        return self.config
    
    def __repr__(self) -> str:
        return f"CustomDataSource(name='{self.name}')"
