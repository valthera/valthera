"""Main Behavioral Cloning (BC) class for Valthera."""

import logging
from typing import Any, Dict, List, Optional, Union
import numpy as np
import yaml
import os

# Make torch optional
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from .base import BaseObservationProcessor, BaseActionProcessor, BasePolicy, BaseDataset, BaseTrainer
from .registry import registry

logger = logging.getLogger(__name__)


class BC:
    """Main Behavioral Cloning class that orchestrates the entire pipeline.
    
    This class provides a high-level interface for behavioral cloning tasks,
    handling data loading, training, evaluation, and deployment.
    """
    
    def __init__(self, domain: str, dataset: Optional[str] = None, 
                 observations: Optional[List[str]] = None, 
                 actions: Optional[List[str]] = None,
                 model: Optional[str] = None,
                 config_path: Optional[str] = None):
        """Initialize the BC pipeline.
        
        Args:
            domain: Domain name (e.g., 'robotics', 'finance', 'gaming')
            dataset: Dataset name to use
            observations: List of observation processor names
            actions: List of action processor names
            model: Model architecture name
            config_path: Path to domain-specific configuration file
        """
        self.domain = domain
        self.dataset_name = dataset
        self.observation_names = observations
        self.action_names = actions
        self.model_name = model
        self.config_path = config_path
        
        # Load domain configuration
        self.config = self._load_domain_config()
        
        # Initialize components
        self._initialize_components()
        
        # Component instances
        self.observation_processors: List[BaseObservationProcessor] = []
        self.action_processors: List[BaseActionProcessor] = []
        self.dataset: Optional[BaseDataset] = None
        self.model: Optional[BasePolicy] = None
        self.trainer: Optional[BaseTrainer] = None
        
        logger.info(f"Initialized BC pipeline for domain: {domain}")
    
    def _load_domain_config(self) -> Dict[str, Any]:
        """Load domain-specific configuration."""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Return default config for the domain
        return self._get_default_domain_config()
    
    def _get_default_domain_config(self) -> Dict[str, Any]:
        """Get default configuration for the domain."""
        if self.domain == "robotics":
            return {
                "dataset": "droid",
                "model": "gru",
                "observations": ["vision", "proprioception"],
                "actions": ["delta_pose"],
                "training": {
                    "batch_size": 32,
                    "learning_rate": 0.0001,
                    "epochs": 100
                }
            }
        elif self.domain == "finance":
            return {
                "dataset": "market_data",
                "model": "mlp",
                "observations": ["tabular"],
                "actions": ["portfolio_weights"],
                "training": {
                    "batch_size": 64,
                    "learning_rate": 0.001,
                    "epochs": 50
                }
            }
        else:
            return {
                "dataset": "default",
                "model": "mlp",
                "observations": ["tabular"],
                "actions": ["continuous"],
                "training": {
                    "batch_size": 32,
                    "learning_rate": 0.001,
                    "epochs": 100
                }
            }
    
    def _initialize_components(self):
        """Initialize components based on configuration."""
        # Get component names from config or use defaults
        dataset_name = self.dataset_name or self.config.get("dataset", "default")
        model_name = self.model_name or self.config.get("model", "mlp")
        observation_names = self.observation_names or self.config.get("observations", ["tabular"])
        action_names = self.action_names or self.config.get("actions", ["continuous"])
        
        # Get components from registry
        try:
            self.dataset = registry.get("dataset", dataset_name)()
            self.model = registry.get("model", model_name)()
            self.trainer = registry.get("trainer", "default")()
            
            # Initialize observation processors
            for obs_name in observation_names:
                processor = registry.get("observation_processor", obs_name)()
                self.observation_processors.append(processor)
            
            # Initialize action processors
            for action_name in action_names:
                processor = registry.get("action_processor", action_name)()
                self.action_processors.append(processor)
                
        except Exception as e:
            logger.warning(f"Could not initialize all components: {e}")
            logger.info("Some components may not be available")
    
    def load_data(self, data_path: str) -> "BC":
        """Load and prepare data for training.
        
        Args:
            data_path: Path to the data
            
        Returns:
            Self for method chaining
        """
        if not self.dataset:
            raise RuntimeError("Dataset not initialized")
        
        logger.info(f"Loading data from: {data_path}")
        
        # Load data using dataset
        self.dataset.load(data_path)
        
        # Fit observation processors if needed
        for processor in self.observation_processors:
            if hasattr(processor, 'fit'):
                processor.fit(self.dataset.get_observations())
        
        # Fit action processors if needed
        for processor in self.action_processors:
            if hasattr(processor, 'fit'):
                processor.fit(self.dataset.get_actions())
        
        logger.info("Data loaded and processors fitted")
        return self
    
    def train(self, train_ratio: float = 0.8, **kwargs) -> Dict[str, Any]:
        """Train the behavioral cloning model.
        
        Args:
            train_ratio: Ratio of data to use for training
            **kwargs: Additional training parameters
            
        Returns:
            Training results
        """
        if not self.trainer or not self.model or not self.dataset:
            raise RuntimeError("Trainer, model, or dataset not initialized")
        
        logger.info("Starting training...")
        
        # Split data
        train_data, val_data = self.dataset.split(train_ratio)
        
        # Train model
        results = self.trainer.train(
            model=self.model,
            train_data=train_data,
            val_data=val_data,
            **kwargs
        )
        
        logger.info("Training completed")
        return results
    
    def evaluate(self, test_data_path: Optional[str] = None) -> Dict[str, float]:
        """Evaluate the trained model.
        
        Args:
            test_data_path: Path to test data (optional)
            
        Returns:
            Evaluation metrics
        """
        if not self.trainer or not self.model:
            raise RuntimeError("Trainer or model not initialized")
        
        logger.info("Evaluating model...")
        
        # Use test data if provided, otherwise use validation data
        if test_data_path:
            test_dataset = registry.get("dataset", "default")()
            test_dataset.load(test_data_path)
            test_data = test_dataset.get_all_data()
        else:
            test_data = self.dataset.get_validation_data()
        
        metrics = self.trainer.evaluate(self.model, test_data)
        
        logger.info(f"Evaluation completed: {metrics}")
        return metrics
    
    def deploy(self, config: Optional[Dict[str, Any]] = None) -> Any:
        """Deploy the trained model.
        
        Args:
            config: Deployment configuration
            
        Returns:
            Deployed model or deployment info
        """
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        logger.info("Deploying model...")
        
        # Simple deployment - return the model
        # In a real implementation, this could involve model serving, etc.
        return self.model
    
    def save(self, path: str) -> None:
        """Save the trained model and configuration.
        
        Args:
            path: Path to save the model
        """
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        logger.info(f"Saving model to: {path}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save model
        if TORCH_AVAILABLE and hasattr(self.model, 'state_dict'):
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'config': self.config
            }, path)
        else:
            # Fallback for non-torch models
            import pickle
            with open(path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'config': self.config
                }, f)
        
        logger.info("Model saved successfully")
    
    def load(self, path: str) -> "BC":
        """Load a saved model and configuration.
        
        Args:
            path: Path to the saved model
            
        Returns:
            Self for method chaining
        """
        logger.info(f"Loading model from: {path}")
        
        if TORCH_AVAILABLE and path.endswith('.pt'):
            checkpoint = torch.load(path, map_location='cpu')
            self.config = checkpoint['config']
            if self.model and hasattr(self.model, 'load_state_dict'):
                self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            # Fallback for non-torch models
            import pickle
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.config = data['config']
                self.model = data['model']
        
        logger.info("Model loaded successfully")
        return self
    
    def predict(self, observations: Union[List, np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Make predictions using the trained model.
        
        Args:
            observations: Input observations
            
        Returns:
            Model predictions
        """
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        # Process observations
        processed_obs = observations
        for processor in self.observation_processors:
            processed_obs = processor.transform(processed_obs)
        
        # Make prediction
        if TORCH_AVAILABLE and torch.is_tensor(processed_obs):
            with torch.no_grad():
                predictions = self.model(processed_obs)
        else:
            predictions = self.model.predict(processed_obs)
        
        # Process actions
        processed_actions = predictions
        for processor in self.action_processors:
            processed_actions = processor.inverse_transform(processed_actions)
        
        return processed_actions
    
    def get_policy(self):
        """Get the trained policy/model."""
        return self.model
