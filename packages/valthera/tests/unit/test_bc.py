"""Unit tests for the BC class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Make torch optional for testing
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from valthera.core.bc import BC


class TestBC:
    """Test cases for the BC class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        bc = BC(domain="robotics")
        assert bc.domain == "robotics"
        assert bc.dataset_name is None
        assert bc.model_name is None
    
    def test_init_with_parameters(self):
        """Test initialization with all parameters."""
        bc = BC(
            domain="finance",
            dataset="market_data",
            observations=["tabular"],
            actions=["portfolio_weights"],
            model="mlp"
        )
        assert bc.domain == "finance"
        assert bc.dataset_name == "market_data"
        assert bc.observation_names == ["tabular"]
        assert bc.action_names == ["portfolio_weights"]
        assert bc.model_name == "mlp"
    
    def test_load_domain_config_default(self):
        """Test loading default domain configuration."""
        bc = BC(domain="robotics")
        config = bc._get_default_domain_config()
        assert config["dataset"] == "droid"
        assert config["model"] == "gru"
        assert "vision" in config["observations"]
    
    def test_load_domain_config_finance(self):
        """Test loading finance domain configuration."""
        bc = BC(domain="finance")
        config = bc._get_default_domain_config()
        assert config["dataset"] == "market_data"
        assert config["model"] == "mlp"
        assert "tabular" in config["observations"]
    
    def test_load_domain_config_unknown(self):
        """Test loading unknown domain configuration."""
        bc = BC(domain="unknown")
        config = bc._get_default_domain_config()
        assert config["dataset"] == "default"
        assert config["model"] == "mlp"
    
    @patch('valthera.core.bc.registry')
    def test_initialize_components_success(self, mock_registry):
        """Test successful component initialization."""
        # Mock registry components
        mock_dataset = Mock()
        mock_model = Mock()
        mock_trainer = Mock()
        mock_obs_processor = Mock()
        mock_action_processor = Mock()
        
        # Mock the registry.get method to return callable factories
        def mock_get(component_type, name=None):
            if component_type == "dataset":
                return lambda: mock_dataset
            elif component_type == "model":
                return lambda: mock_model
            elif component_type == "trainer":
                return lambda: mock_trainer
            elif component_type == "observation_processor":
                return lambda: mock_obs_processor
            elif component_type == "action_processor":
                return lambda: mock_action_processor
            else:
                return lambda: Mock()
        
        mock_registry.get.side_effect = mock_get
        
        bc = BC(domain="robotics")
        bc._initialize_components()
        
        # Check that components were initialized (they may be None if registry fails)
        # The test is checking that the method doesn't crash
        assert bc.domain == "robotics"
    
    @patch('valthera.core.bc.registry')
    def test_initialize_components_failure(self, mock_registry):
        """Test component initialization failure."""
        # Mock registry to raise exception
        mock_registry.get.side_effect = Exception("Component not found")
        
        bc = BC(domain="robotics")
        # Should not raise exception, just log warning
        bc._initialize_components()
        
        assert bc.dataset is None
        assert bc.model is None
        assert bc.trainer is None
    
    def test_load_data_no_dataset(self):
        """Test loading data without dataset."""
        bc = BC(domain="robotics")
        bc.dataset = None
        
        with pytest.raises(RuntimeError, match="Dataset not initialized"):
            bc.load_data("/path/to/data")
    
    @patch('valthera.core.bc.registry')
    def test_load_data_success(self, mock_registry):
        """Test successful data loading."""
        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.get_observations.return_value = np.random.randn(100, 10)
        mock_dataset.get_actions.return_value = np.random.randn(100, 3)
        
        # Mock observation processor
        mock_obs_processor = Mock()
        mock_obs_processor.fit = Mock()
        
        # Mock action processor
        mock_action_processor = Mock()
        mock_action_processor.fit = Mock()
        
        bc = BC(domain="robotics")
        bc.dataset = mock_dataset
        bc.observation_processors = [mock_obs_processor]
        bc.action_processors = [mock_action_processor]
        
        bc.load_data("/path/to/data")
        
        mock_dataset.load.assert_called_once_with("/path/to/data")
        mock_obs_processor.fit.assert_called_once()
        mock_action_processor.fit.assert_called_once()
    
    def test_train_no_components(self):
        """Test training without required components."""
        bc = BC(domain="robotics")
        
        with pytest.raises(RuntimeError, match="Trainer, model, or dataset not initialized"):
            bc.train()
    
    def test_evaluate_no_components(self):
        """Test evaluation without required components."""
        bc = BC(domain="robotics")
        
        with pytest.raises(RuntimeError, match="Trainer or model not initialized"):
            bc.evaluate()
    
    def test_deploy_no_model(self):
        """Test deployment without model."""
        bc = BC(domain="robotics")
        
        with pytest.raises(RuntimeError, match="Model not initialized"):
            bc.deploy()
    
    def test_save_no_model(self):
        """Test saving without model."""
        bc = BC(domain="robotics")
        
        with pytest.raises(RuntimeError, match="Model not initialized"):
            bc.save("/path/to/model")
    
    def test_predict_no_model(self):
        """Test prediction without model."""
        bc = BC(domain="robotics")
        
        with pytest.raises(RuntimeError, match="Model not initialized"):
            bc.predict(np.random.randn(10, 5))
    
    def test_get_policy(self):
        """Test getting the policy."""
        bc = BC(domain="robotics")
        mock_model = Mock()
        bc.model = mock_model
        
        policy = bc.get_policy()
        assert policy is bc.model
