from valthera.connectors.base import BaseConnector


class MockPostHogConnector(BaseConnector):
    """
    High usage and sufficient session_count -> saturates usage & recency factors for motivation.
    """
    def get_user_data(self, user_id: str):
        return {
            "distinct_ids": [user_id, f"email_{user_id}"],
            "last_event_timestamp": "2023-09-20T12:34:56Z",
            "feature_flags": ["beta_dashboard", "early_access"],
            "session_count": 30,                  # e.g. min(session_count/5, 1.0) => 30/5=6 => saturates at 1.0
            "avg_session_duration_sec": 400,
            "recent_event_types": ["pageview", "button_click", "premium_feature_used"],
            "events_count_past_30days": 80,       # min(80, 50)=50 => usage_factor=1.0 in your code
            "onboarding_steps_completed": 5       # Or 5 if you want high ability too
        }
