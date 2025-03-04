import os
import requests
from typing import Dict, Any, List

from valthera.connectors.base import BaseConnector


class PosthogConnector(BaseConnector):
    """
    A flexible connector that retrieves usage events or analytics from PostHog.

    Prerequisites:
      - POSTHOG_HOST: The base URL of your PostHog instance (e.g. "https://app.posthog.com")
      - POSTHOG_API_KEY: A personal or project API key for PostHog
      - POSTHOG_PROJECT_ID: The numeric ID of your PostHog project

    Usage:
        connector = PosthogConnector()
        user_data = connector.get_user_data("some_user_id")

    Customizing:
      - Override `get_events_endpoint()` to change how events are retrieved (e.g., /insights).
      - Override `parse_response_data(...)` to transform the raw response in a custom way.
      - Override `build_params(...)` if you need different query parameters (limit, date range, etc.).
    """

    def __init__(self):
        # In a real scenario, store these as environment variables or config
        self.host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
        self.api_key = os.getenv("POSTHOG_API_KEY")      # e.g., "phc_abc123..."
        self.project_id = os.getenv("POSTHOG_PROJECT_ID")  # e.g., "1234"
        if not self.api_key or not self.project_id:
            raise ValueError("Missing PostHog credentials: POSTHOG_API_KEY or POSTHOG_PROJECT_ID.")

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Query PostHog to retrieve relevant analytics or usage data for the user.

        :param user_id: A unique identifier for the user
                        (may be an email, userId, or distinct_id in PostHog).
        :return: A dictionary of usage or engagement metrics.
        """
        endpoint = self.get_events_endpoint()
        headers = self.build_headers()
        params = self.build_params(user_id)

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()  # raw dictionary from PostHog

            return self.parse_response_data(user_id, data)

        except requests.exceptions.HTTPError as http_err:
            print(f"PostHog API HTTP error: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Error connecting to PostHog: {req_err}")
        except Exception as ex:
            print(f"Unexpected error retrieving PostHog data for {user_id}: {ex}")

        # Return empty dict if error occurs
        return {}

    def get_events_endpoint(self) -> str:
        """
        Returns the default endpoint for retrieving events in PostHog.
        Override this if you want to use /insights or another endpoint.
        """
        return f"{self.host}/api/projects/{self.project_id}/events/"

    def build_headers(self) -> Dict[str, str]:
        """
        Returns the HTTP headers used in the GET request.
        Override if you need to modify the auth or content type.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def build_params(self, user_id: str) -> Dict[str, Any]:
        """
        Returns the default query parameters for retrieving events.
        Override if you need date ranges, event filters, or a bigger limit, etc.
        """
        return {
            # If you store user_id as the "person_id" or "distinct_id" in PostHog
            "person_id": user_id,
            "limit": 50
        }

    def parse_response_data(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform the raw response from PostHog into a final dictionary
        that your application can easily consume.

        The default logic here:
          - Expects a list of events under data["results"]
            (or returns an empty list if missing).
          - Extracts total event count, first/last event timestamps,
            and the distinct event types.

        Override this if you want to parse additional fields,
        or store data differently.
        """
        events = data.get("results", [])

        usage_summary = {
            "user_id": user_id,
            "total_events": len(events),
            "first_event_timestamp": None,
            "last_event_timestamp": None,
            "distinct_event_types": []
        }

        if events:
            # Sort by timestamp (if present) to find first/last
            sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))
            usage_summary["first_event_timestamp"] = sorted_events[0].get("timestamp")
            usage_summary["last_event_timestamp"] = sorted_events[-1].get("timestamp")

            # Gather distinct event names
            event_names = [ev.get("event") for ev in events if ev.get("event")]
            usage_summary["distinct_event_types"] = list(set(event_names))

        return usage_summary
