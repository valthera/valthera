import requests
from typing import Dict, Any, Optional


class GenericApiConnector:
    """
    A generic connector for REST APIs using the requests library.

    This base class provides:
      - URL construction based on a base_url.
      - Common header building (including support for API keys).
      - Methods for GET and POST requests with basic error handling.

    Specific API connectors can inherit from this class and add custom methods
    or override these methods as needed.
    """
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        """
        :param base_url: The base URL for the API (e.g., "https://api.example.com")
        :param api_key: Optional API key for authentication (if required)
        :param timeout: Timeout for API requests in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

    def build_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Constructs HTTP headers for the request.
        Override or extend this method if your API needs additional headers.
        """
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def build_url(self, endpoint: str) -> str:
        """
        Constructs the full URL by combining the base URL with the given endpoint.

        :param endpoint: The API endpoint path (should start with '/')
        """
        return f"{self.base_url}{endpoint}"

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes a GET request to the specified API endpoint.

        :param endpoint: API endpoint (e.g., "/users")
        :param params: URL query parameters as a dictionary
        :param headers: Additional headers to include in the request
        :return: The JSON response as a dictionary, or an empty dict on error
        """
        url = self.build_url(endpoint)
        all_headers = self.build_headers(headers)
        try:
            response = requests.get(url, params=params, headers=all_headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Error connecting to API: {req_err}")
        except Exception as err:
            print(f"Unexpected error: {err}")

        return {}

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes a POST request to the specified API endpoint.

        :param endpoint: API endpoint (e.g., "/data")
        :param data: The JSON body to send with the request
        :param headers: Additional headers to include in the request
        :return: The JSON response as a dictionary, or an empty dict on error
        """
        url = self.build_url(endpoint)
        all_headers = self.build_headers(headers)
        try:
            response = requests.post(url, json=data, headers=all_headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Error connecting to API: {req_err}")
        except Exception as err:
            print(f"Unexpected error: {err}")

        return {}
