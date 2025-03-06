import unittest
from unittest.mock import Mock
from valthera.models import User
from valthera.valthera.utils.aggregator import DataAggregator


class TestDataAggregator(unittest.TestCase):
    def setUp(self):
        self.mock_connector = Mock()
        self.mock_connector.get_user_data.return_value = {"test_key": "test_value"}
        self.aggregator = DataAggregator({"mock": self.mock_connector})

    def test_build_user_context(self):
        user = User(user_id="123", email="test@example.com")
        user_context = self.aggregator.build_user_context(user)
        self.assertEqual(user_context.user_id, "123")
        self.assertIn("mock_test_key", user_context.connector_data)


if __name__ == "__main__":
    unittest.main()
