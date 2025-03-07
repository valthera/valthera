import os
from langchain_valthera.tools import ValtheraTool, ValtheraToolInput
from langchain_valthera.tools import ConnectorData, BehaviorModel  # Import additional models

if __name__ == "__main__":
    # Initialize ValtheraTool using langchain_valthera without additional configuration parameters
    valthera_tool = ValtheraTool()

    # Test input using the updated schema:
    test_input = ValtheraToolInput(
        user_id="user_12345",
        connector_data=ConnectorData(data={
            "email": "sam@example.com",
            "hubspot_contact_id": "999-ZZZ",
            "lifecycle_stage": "opportunity",
            "lead_status": "engaged",
            "lead_score": 100,
            "company_name": "MaxMotivation Corp.",
            "marketing_emails_opened": 20,
            "session_count": 30,
            "events_count_past_30days": 80,
            "onboarding_steps_completed": 5
        }),
        behavior=BehaviorModel(
            behavior_id="behavior_onboarding_1",
            name="Finish Onboarding",
            description="Complete any remaining onboarding steps."
        )
    )

    # Run tool using the updated _run signature
    result = valthera_tool._run(
        user_id=test_input.user_id,
        connector_data=test_input.connector_data,
        behavior=test_input.behavior
    )

    # Print output
    print("=== Valthera Tool Output ===")
    print(result)
