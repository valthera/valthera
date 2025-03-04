from abc import ABC, abstractmethod
from typing import Dict


class BaseConnector(ABC):
    """
    A base class for all data connectors.
    Ensures a common interface for retrieving user data.
    """

    @abstractmethod
    def get_user_data(self, user_id: str) -> Dict:
        """
        Retrieves data for the specified user (e.g. from an external API or database).

        :param user_id: The user's unique identifier.
        :return: A dictionary containing relevant user data.
        """
        pass
