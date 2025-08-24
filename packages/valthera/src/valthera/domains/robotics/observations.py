"""Robotics domain observation processors for Valthera."""

import logging
from typing import Any, Dict, List, Optional, Union
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import numpy as np
from PIL import Image

from ...core.base import BaseObservationProcessor
from ...core.registry import register_component

logger = logging.getLogger(__name__)


@register_component("observation_processor", "vision", is_default=True)
class VisionProcessor(BaseObservationProcessor):
    """Vision processor for RGB and depth images."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.image_size = config.get("image_size", (64, 64))
        self.normalize = config.get("normalize", True)
        self.use_depth = config.get("use_depth", True)
        self.feature_dim = config.get("feature_dim", 512)
        
        # Initialize vision encoder
        self.encoder = self._create_encoder()
        
        # Image transforms
        self.transforms = transforms.Compose([
            transforms.Resize(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) if self.normalize else transforms.Lambda(lambda x: x)
        ])
    
    def _create_encoder(self) -> nn.Module:
        """Create vision encoder network."""
        # Simple CNN encoder
        encoder = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            
            nn.Flatten(),
            nn.Linear(256, self.feature_dim),
            nn.ReLU()
        )
        
        return encoder
    
    def fit(self, observations: Union[List, np.ndarray, torch.Tensor]) -> "VisionProcessor":
        """Fit the processor to the observation data."""
        # For vision, we don't need to fit anything specific
        # The encoder is pre-defined
        self._is_fitted = True
        return self
    
    def transform(self, observations: Union[List, np.ndarray, torch.Tensor]) -> torch.Tensor:
        """Transform observations to the format expected by the model."""
        if not self._is_fitted:
            raise ValueError("Processor not fitted. Call fit() first.")
        
        if isinstance(observations, list):
            # Handle list of observation dictionaries
            processed_obs = []
            for obs in observations:
                if isinstance(obs, dict) and "rgb" in obs:
                    # Load and process RGB image
                    if isinstance(obs["rgb"], str):
                        # File path
                        img = Image.open(obs["rgb"]).convert('RGB')
                    else:
                        # Already PIL image
                        img = obs["rgb"]
                    
                    # Apply transforms
                    img_tensor = self.transforms(img)
                    
                    # Add depth if available
                    if self.use_depth and "depth" in obs:
                        depth = obs["depth"]
                        if isinstance(depth, str):
                            # File path
                            depth_array = np.load(depth)
                        else:
                            depth_array = depth
                        
                        # Normalize depth
                        depth_tensor = torch.tensor(depth_array, dtype=torch.float32)
                        depth_tensor = depth_tensor.unsqueeze(0)  # Add channel dimension
                        
                        # Combine RGB and depth
                        img_tensor = torch.cat([img_tensor, depth_tensor], dim=0)
                    
                    processed_obs.append(img_tensor)
                else:
                    # Fallback for non-vision observations
                    processed_obs.append(torch.zeros(3, *self.image_size))
            
            # Stack into batch
            if processed_obs:
                batch = torch.stack(processed_obs)
                # Encode through vision network
                with torch.no_grad():
                    features = self.encoder(batch)
                return features
            else:
                return torch.zeros(0, self.feature_dim)
        
        elif isinstance(observations, np.ndarray):
            # Handle numpy array
            if observations.ndim == 3:
                # Single image
                img = Image.fromarray(observations)
                img_tensor = self.transforms(img).unsqueeze(0)
            elif observations.ndim == 4:
                # Batch of images
                img_tensors = []
                for img_array in observations:
                    img = Image.fromarray(img_array)
                    img_tensor = self.transforms(img)
                    img_tensors.append(img_tensor)
                img_tensor = torch.stack(img_tensors)
            else:
                raise ValueError(f"Unexpected observation shape: {observations.shape}")
            
            # Encode through vision network
            with torch.no_grad():
                features = self.encoder(img_tensor)
            return features
        
        elif isinstance(observations, torch.Tensor):
            # Handle torch tensor
            if observations.dim() == 3:
                # Single image
                observations = observations.unsqueeze(0)
            
            # Encode through vision network
            with torch.no_grad():
                features = self.encoder(observations)
            return features
        
        else:
            raise TypeError(f"Unsupported observation type: {type(observations)}")
    
    def inverse_transform(self, processed_observations: torch.Tensor) -> torch.Tensor:
        """Inverse transform processed observations back to original format."""
        # This is a simplified inverse transform
        return processed_observations


@register_component("observation_processor", "proprioception")
class ProprioceptionProcessor(BaseObservationProcessor):
    """Proprioception processor for joint positions and robot state."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.joint_names = config.get("joint_names", [])
        self.feature_dim = config.get("feature_dim", 64)
        self.normalize = config.get("normalize", True)
        
        # Statistics for normalization
        self.joint_mean = None
        self.joint_std = None
        
        # Simple MLP encoder for proprioception
        self.encoder = nn.Sequential(
            nn.Linear(100, 128),  # Assume max 100 joint features
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, self.feature_dim),
            nn.ReLU()
        )
    
    def fit(self, observations: Union[List, np.ndarray, torch.Tensor]) -> "ProprioceptionProcessor":
        """Fit the processor to the observation data."""
        # Extract joint positions from observations
        joint_data = []
        
        if isinstance(observations, list):
            for obs in observations:
                if isinstance(obs, dict):
                    # Look for joint-related keys
                    for key, value in obs.items():
                        if "joint" in key.lower() or "proprio" in key.lower():
                            if isinstance(value, (str, np.ndarray)):
                                if isinstance(value, str):
                                    # File path
                                    joint_array = np.load(value)
                                else:
                                    joint_array = value
                                joint_data.append(joint_array.flatten())
        
        if joint_data:
            joint_data = np.array(joint_data)
            
            # Compute statistics for normalization
            if self.normalize:
                self.joint_mean = np.mean(joint_data, axis=0)
                self.joint_std = np.std(joint_data, axis=0)
                # Avoid division by zero
                self.joint_std = np.where(self.joint_std == 0, 1.0, self.joint_std)
        
        self._is_fitted = True
        return self
    
    def transform(self, observations: Union[List, np.ndarray, torch.Tensor]) -> torch.Tensor:
        """Transform observations to the format expected by the model."""
        if not self._is_fitted:
            raise ValueError("Processor not fitted. Call fit() first.")
        
        if isinstance(observations, list):
            # Handle list of observation dictionaries
            processed_obs = []
            for obs in observations:
                if isinstance(obs, dict):
                    # Extract joint features
                    joint_features = self._extract_joint_features(obs)
                    processed_obs.append(joint_features)
                else:
                    # Fallback
                    processed_obs.append(torch.zeros(self.feature_dim))
            
            # Stack into batch
            if processed_obs:
                batch = torch.stack(processed_obs)
                # Encode through proprioception network
                with torch.no_grad():
                    features = self.encoder(batch)
                return features
            else:
                return torch.zeros(0, self.feature_dim)
        
        elif isinstance(observations, np.ndarray):
            # Handle numpy array
            if observations.ndim == 1:
                # Single observation
                observations = observations.reshape(1, -1)
            
            # Encode through proprioception network
            observations_tensor = torch.tensor(observations, dtype=torch.float32)
            with torch.no_grad():
                features = self.encoder(observations_tensor)
            return features
        
        elif isinstance(observations, torch.Tensor):
            # Handle torch tensor
            if observations.dim() == 1:
                observations = observations.unsqueeze(0)
            
            # Encode through proprioception network
            with torch.no_grad():
                features = self.encoder(observations)
            return features
        
        else:
            raise TypeError(f"Unsupported observation type: {type(observations)}")
    
    def _extract_joint_features(self, obs: Dict[str, Any]) -> torch.Tensor:
        """Extract joint features from observation."""
        joint_features = []
        
        for key, value in obs.items():
            if "joint" in key.lower() or "proprio" in key.lower():
                if isinstance(value, str):
                    # File path
                    joint_array = np.load(value)
                else:
                    joint_array = value
                
                # Flatten and normalize
                joint_flat = joint_array.flatten()
                if self.normalize and self.joint_mean is not None:
                    joint_flat = (joint_flat - self.joint_mean) / self.joint_std
                
                joint_features.extend(joint_flat)
        
        # Pad or truncate to expected size
        if len(joint_features) < 100:
            joint_features.extend([0.0] * (100 - len(joint_features)))
        else:
            joint_features = joint_features[:100]
        
        return torch.tensor(joint_features, dtype=torch.float32)
    
    def inverse_transform(self, processed_observations: torch.Tensor) -> torch.Tensor:
        """Inverse transform processed observations back to original format."""
        # This is a simplified inverse transform
        return processed_observations
