"""Interface definitions for Valthera components."""

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


class ObservationInterface(ABC):
    """Interface for observation processing components."""
    
    @abstractmethod
    def process(self, observations: Union[List, np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Process observations."""
        pass
    
    @abstractmethod
    def get_features(self) -> Union[np.ndarray, "torch.Tensor"]:
        """Get processed features."""
        pass


class ActionInterface(ABC):
    """Interface for action processing components."""
    
    @abstractmethod
    def process(self, actions: Union[List, np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Process actions."""
        pass
    
    @abstractmethod
    def get_output(self) -> Union[np.ndarray, "torch.Tensor"]:
        """Get processed output."""
        pass


class DatasetInterface(ABC):
    """Interface for dataset components."""
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load dataset from path."""
        pass
    
    @abstractmethod
    def get_batch(self, batch_size: int) -> tuple:
        """Get a batch of data."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get dataset size."""
        pass


class ModelInterface(ABC):
    """Interface for model components."""
    
    @abstractmethod
    def forward(self, inputs: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Forward pass through the model."""
        pass
    
    @abstractmethod
    def predict(self, inputs: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Make predictions."""
        pass


class TrainerInterface(ABC):
    """Interface for trainer components."""
    
    @abstractmethod
    def train(self, model: Any, train_data: Any, val_data: Any, **kwargs) -> Dict[str, Any]:
        """Train the model."""
        pass
    
    @abstractmethod
    def evaluate(self, model: Any, test_data: Any) -> Dict[str, float]:
        """Evaluate the model."""
        pass


class EvaluatorInterface(ABC):
    """Interface for evaluator components."""
    
    @abstractmethod
    def evaluate(self, model: Any, test_data: Any) -> Dict[str, float]:
        """Evaluate the model."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """Get evaluation metrics."""
        pass


class DeploymentInterface(ABC):
    """Interface for deployment components."""
    
    @abstractmethod
    def deploy(self, model: Any, config: Dict[str, Any]) -> Any:
        """Deploy the model."""
        pass
    
    @abstractmethod
    def predict(self, inputs: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Make predictions using deployed model."""
        pass
    
    def shutdown(self) -> None:
        """Shutdown the deployment."""
        pass
