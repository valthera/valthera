from valthera.connectors.base import BaseConnector
from valthera.models import User, UserContext
from typing import Dict, Any


class DataAggregator:
    def __init__(self, connectors: Dict[str, BaseConnector]):
        self.connectors = connectors

    def build_user_context(self, user: User) -> UserContext:
        connector_data = {}

        # Dynamically fetch user data from each connector.
        for name, connector in self.connectors.items():
            data = connector.get_user_data(user.user_id)
            if isinstance(data, dict):
                # Flatten nested data with a prefix to avoid key collisions
                flattened_data = self._flatten_dict(data, prefix=f"{name}_")
                connector_data.update(flattened_data)
            else:
                # Store non-dict values directly
                connector_data[name] = data

        return UserContext(
            user_id=user.user_id,
            connector_data=connector_data
        )

    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flattens a nested dictionary by prefixing keys with their parent keys.
        Example: {"hubspot": {"lead_score": 50}} -> {"hubspot_lead_score": 50}
        """
        flattened = {}
        for key, value in d.items():
            new_key = f"{prefix}{key}"
            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, prefix=f"{new_key}_"))
            else:
                flattened[new_key] = value
        return flattened
