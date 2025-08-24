"""Abstract base classes for Valthera components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

# Make torch optional
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

import numpy as np


class BaseComponent:
    """Base class for all Valthera components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the component.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._is_initialized = False
    
    def get_config(self) -> Dict[str, Any]:
        """Get the component configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the component configuration.
        
        Args:
            new_config: New configuration to merge
        """
        self.config.update(new_config)
    
    def is_initialized(self) -> bool:
        """Check if the component is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._is_initialized
    
    def __str__(self) -> str:
        """String representation of the component."""
        return f"{self.__class__.__name__}(config={self.config})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the component."""
        return f"{self.__class__.__name__}(config={self.config}, initialized={self._is_initialized})"


class BaseObservationProcessor(ABC):
    """Abstract base class for observation processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.is_fitted = False
    
    @abstractmethod
    def fit(self, observations: Union[List, np.ndarray, "torch.Tensor"]) -> None:
        """Fit the processor to the observations.
        
        Args:
            observations: Training observations
        """
        pass
    
    @abstractmethod
    def transform(self, observations: Union[List, np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Transform observations.
        
        Args:
            observations: Input observations
            
        Returns:
            Transformed observations
        """
        pass
    
    def inverse_transform(self, processed_observations: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Inverse transform processed observations.
        
        Args:
            processed_observations: Processed observations
            
        Returns:
            Original observations
        """
        # Default implementation - override if needed
        return processed_observations


class BaseActionProcessor(ABC):
    """Abstract base class for action processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.is_fitted = False
    
    @abstractmethod
    def fit(self, actions: Union[List, np.ndarray, "torch.Tensor"]) -> None:
        """Fit the processor to the actions.
        
        Args:
            actions: Training actions
        """
        pass
    
    @abstractmethod
    def transform(self, actions: Union[List, np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Transform actions.
        
        Args:
            actions: Input actions
            
        Returns:
            Transformed actions
        """
        pass
    
    def inverse_transform(self, processed_actions: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Inverse transform processed actions.
        
        Args:
            processed_actions: Processed actions
            
        Returns:
            Original actions
        """
        # Default implementation - override if needed
        return processed_actions


class BasePolicy(ABC):
    """Abstract base class for policies/models."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the policy.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def forward(self, observations: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Forward pass through the policy.
        
        Args:
            observations: Input observations
            
        Returns:
            Policy outputs
        """
        pass
    
    def predict(self, observations: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Make predictions (alias for forward).
        
        Args:
            observations: Input observations
            
        Returns:
            Predictions
        """
        return self.forward(observations)
    
    def save(self, path: str) -> None:
        """Save the model.
        
        Args:
            path: Path to save the model
        """
        if TORCH_AVAILABLE and hasattr(self, 'state_dict'):
            torch.save(self.state_dict(), path)
        else:
            # Fallback for non-torch models
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(self, f)
    
    def load(self, path: str) -> None:
        """Load the model.
        
        Args:
            path: Path to load the model from
        """
        if TORCH_AVAILABLE and path.endswith('.pt'):
            if hasattr(self, 'load_state_dict'):
                state_dict = torch.load(path, map_location='cpu')
                self.load_state_dict(state_dict)
        else:
            # Fallback for non-torch models
            import pickle
            with open(path, 'rb') as f:
                data = pickle.load(f)
                # Update instance attributes
                for key, value in data.__dict__.items():
                    setattr(self, key, value)


class BaseDataset(ABC):
    """Abstract base class for datasets."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the dataset.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.data = None
        self.metadata = {}
    
    @abstractmethod
    def load(self, data_path: str) -> None:
        """Load data from the specified path.
        
        Args:
            data_path: Path to the data
        """
        pass
    
    def split(self, train_ratio: float = 0.8) -> tuple:
        """Split the dataset into train and validation sets.
        
        Args:
            train_ratio: Ratio of data to use for training
            
        Returns:
            Tuple of (train_data, val_data)
        """
        if self.data is None:
            raise RuntimeError("No data loaded")
        
        # Default implementation - override if needed
        split_idx = int(len(self.data) * train_ratio)
        train_data = self.data[:split_idx]
        val_data = self.data[split_idx:]
        
        return train_data, val_data
    
    def get_observations(self) -> Union[np.ndarray, "torch.Tensor"]:
        """Get all observations from the dataset.
        
        Returns:
            Observations
        """
        if self.data is None:
            raise RuntimeError("No data loaded")
        
        # Default implementation - override if needed
        return self.data.get('observations', self.data)
    
    def get_actions(self) -> Union[np.ndarray, "torch.Tensor"]:
        """Get all actions from the dataset.
        
        Returns:
            Actions
        """
        if self.data is None:
            raise RuntimeError("No data loaded")
        
        # Default implementation - override if needed
        return self.data.get('actions', self.data)
    
    def get_validation_data(self) -> Any:
        """Get validation data.
        
        Returns:
            Validation data
        """
        _, val_data = self.split()
        return val_data
    
    def get_all_data(self) -> Any:
        """Get all data.
        
        Returns:
            All data
        """
        return self.data
    
    def __len__(self) -> int:
        """Get the length of the dataset.
        
        Returns:
            Number of samples
        """
        if self.data is None:
            return 0
        return len(self.data)


class BaseTrainer(ABC):
    """Abstract base class for trainers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the trainer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.model = None
        self.optimizer = None
        self.scheduler = None
    
    @abstractmethod
    def train(self, model: BasePolicy, train_data: Any, val_data: Any, **kwargs) -> Dict[str, Any]:
        """Train the model.
        
        Args:
            model: Model to train
            train_data: Training data
            val_data: Validation data
            **kwargs: Additional training parameters
            
        Returns:
            Training results
        """
        pass
    
    @abstractmethod
    def evaluate(self, model: BasePolicy, test_data: Any) -> Dict[str, float]:
        """Evaluate the model.
        
        Args:
            model: Model to evaluate
            test_data: Test data
            
        Returns:
            Evaluation metrics
        """
        pass
    
    def save_checkpoint(self, path: str, **kwargs) -> None:
        """Save a training checkpoint.
        
        Args:
            path: Path to save the checkpoint
            **kwargs: Additional data to save
        """
        checkpoint = {
            'model_state_dict': self.model.state_dict() if TORCH_AVAILABLE and hasattr(self.model, 'state_dict') else None,
            'optimizer_state_dict': self.optimizer.state_dict() if self.optimizer else None,
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            **kwargs
        }
        
        if TORCH_AVAILABLE:
            torch.save(checkpoint, path)
        else:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(checkpoint, f)
    
    def load_checkpoint(self, path: str) -> None:
        """Load a training checkpoint.
        
        Args:
            path: Path to load the checkpoint from
        """
        if TORCH_AVAILABLE and path.endswith('.pt'):
            checkpoint = torch.load(path, map_location='cpu')
        else:
            import pickle
            with open(path, 'rb') as f:
                checkpoint = pickle.load(f)
        
        if self.model and checkpoint["model_state_dict"]:
            if hasattr(self.model, 'load_state_dict'):
                self.model.load_state_dict(checkpoint["model_state_dict"])
        
        if self.optimizer and checkpoint["optimizer_state_dict"]:
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
        if self.scheduler and checkpoint["scheduler_state_dict"]:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
