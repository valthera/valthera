from valthera.connectors.base import BaseConnector


class MockSnowflakeConnector(BaseConnector):
    """
    Other user profile data (not as crucial for motivation, 
    but consistent with a highly engaged user).
    """
    def get_user_data(self, user_id: str):
        return {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "subscription_status": "paid",
            "plan_tier": "premium",
            "account_creation_date": "2023-01-01",
            "preferred_language": "en",
            "last_login_datetime": "2023-09-20T12:00:00Z"
        }

