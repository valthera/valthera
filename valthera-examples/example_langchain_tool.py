from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

# Import Valthera models and agents (assumes these modules are in your environment)
from valthera.models import UserContext
from valthera.agents.behavioral.fogg_model.trigger_decision_agent.agent import TriggerDecisionAgent  # Adjust as needed


class BehaviorModel(BaseModel):
    behavior_id: str = Field(..., description="Unique identifier for the behavior")
    name: str = Field(..., description="Name of the behavior")
    description: str = Field(..., description="Detailed description of the behavior")


class ConnectorData(BaseModel):
    """
    ConnectorData encapsulates connector-specific data.
    Customize this model by adding additional fields as required.
    """
    data: Dict[str, Any] = Field(default_factory=dict, description="Connector-specific data")


class ValtheraToolInput(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    connector_data: ConnectorData = Field(..., description="Structured connector data")
    behavior: BehaviorModel = Field(..., description="Behavior details including id, name, and description")


class ValtheraTool(BaseTool):
    """
    ValtheraTool

    This tool leverages the Valthera Fogg model-based decision engine to determine
    if a trigger should be sent to a user for a specific behavior. It takes user context
    and behavior details as input, scores the user's state, and returns a trigger recommendation.
    """
    name: str = "ValtheraTool"
    description: str = (
        "Determines if a trigger should be sent based on the Fogg model using Valthera's "
        "scoring and reasoning engine."
    )
    args_schema: Type[BaseModel] = ValtheraToolInput

    def _run(
        self,
        user_id: str,
        connector_data: ConnectorData,
        behavior: BehaviorModel,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        # Define behavior weights if needed (customize as necessary)
        behavior_weights: List[Dict[str, Any]] = []
        
        # Instantiate the trigger decision agent.
        agent = TriggerDecisionAgent(behavior_weights=behavior_weights)
        
        # Create a UserContext and a behavior object from the provided data.
        user_context_obj = UserContext(
            user_id=user_id,
            connector_data=connector_data.dict()  # Convert ConnectorData to a dict
        )
        # Ensure behavior is in the proper format.
        behavior_obj = BehaviorModel(**behavior.dict())
        
        # Run the agent to get a trigger recommendation.
        recommendation = agent.run(user_context_obj, behavior_obj)
        
        if recommendation is None:
            return "No trigger recommendation."
        
        # Extract trigger details from the recommendation.
        if isinstance(recommendation, dict):
            trigger_message = recommendation.get("trigger_message", "No trigger message")
            confidence = recommendation.get("confidence")
            channel = recommendation.get("channel")
            rationale = recommendation.get("rationale")
        else:
            trigger_message = recommendation.trigger_message
            confidence = recommendation.confidence
            channel = recommendation.channel
            rationale = recommendation.rationale
        
        result = f"Trigger: {trigger_message}"
        if confidence is not None:
            result += f", Confidence: {confidence}"
        if channel:
            result += f", Channel: {channel}"
        if rationale:
            result += f", Rationale: {rationale}"
        return result

    async def _arun(
        self,
        input_data: dict,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        # Parse the input data using the defined args_schema.
        parsed_input = self.args_schema.parse_obj(input_data)
        return self._run(
            user_id=parsed_input.user_id,
            connector_data=parsed_input.connector_data,
            behavior=parsed_input.behavior,
            run_manager=run_manager
        )


# === 🚀 TESTING THE LANGCHAIN TOOL ===
if __name__ == "__main__":
    # Test input using the updated schema. Note that email and other user-specific data
    # are now included inside the connector_data.
    test_input = ValtheraToolInput(
        user_id="user_12345",
        connector_data=ConnectorData(data={
            "hubspot_contact_id": "999-ZZZ",
            "lifecycle_stage": "opportunity",
            "lead_status": "engaged",
            "lead_score": 100,
            "company_name": "MaxMotivation Corp.",
            "marketing_emails_opened": 20,
            "session_count": 30,
            "events_count_past_30days": 80,
            "onboarding_steps_completed": 5,
            "email": "sam@example.com"
        }),
        behavior=BehaviorModel(
            behavior_id="behavior_onboarding_1",
            name="Finish Onboarding",
            description="Complete any remaining onboarding steps."
        )
    )
    
    tool = ValtheraTool()
    result = tool._run(
        user_id=test_input.user_id,
        connector_data=test_input.connector_data,
        behavior=test_input.behavior
    )
    print("=== Valthera Tool Output ===")
    print(result)
