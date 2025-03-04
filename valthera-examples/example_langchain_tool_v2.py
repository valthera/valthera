import os
from langchain_valthera.tools import ValtheraTool, ValtheraToolInput


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

    # Initialize ValtheraTool using langchain_valthera
    valthera_tool = ValtheraTool(
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
