import os
from typing import List, Dict, Any, Optional
from valthera.connectors.generic_api_connector import GenericApiConnector  # Make sure the path is correct


class GenericHubSpotConnector(GenericApiConnector):
    """
    A configurable connector for HubSpot built on top of the GenericApiConnector.
    You can pass the object type (e.g. "contacts", "custom_objects") and
    a list of properties to fetch.

    This connector constructs the appropriate HubSpot v3 endpoint and parses the response.
    """
    def __init__(
        self,
        object_type: str = "contacts",
        properties: Optional[List[str]] = None
    ):
        access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("Missing HUBSPOT_ACCESS_TOKEN in environment variables.")

        # HubSpot's base API URL for v3 endpoints
        base_url = "https://api.hubapi.com"
        # Initialize the GenericApiConnector with the HubSpot base URL and access token as the API key.
        super().__init__(base_url=base_url, api_key=access_token)

        self.object_type = object_type
        # Set default properties if none provided; these can be customized per use case.
        self.properties = properties if properties is not None else [
            "email", "firstname", "lastname", "company", "jobtitle"
        ]

    def transform_data(self, object_id: str, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform the raw properties dict into your desired structure.
        Customize this method if needed.
        """
        transformed = {"object_id": object_id}
        for prop in self.properties:
            transformed[prop] = props.get(prop)
        return transformed

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user data from HubSpot by making a GET request to the appropriate endpoint.

        For contacts: GET /crm/v3/objects/contacts/{user_id}?properties=prop1,prop2,...
        For custom objects: GET /crm/v3/objects/{object_type}/{user_id}?properties=...
        """
        # Build a comma-separated string of properties.
        properties_str = ",".join(self.properties)
        endpoint = f"/crm/v3/objects/{self.object_type}/{user_id}"
        params = {"properties": properties_str}

        response = self.get(endpoint, params=params)
        # HubSpot returns the properties under the "properties" key.
        props = response.get("properties", {})
        return self.transform_data(user_id, props)
