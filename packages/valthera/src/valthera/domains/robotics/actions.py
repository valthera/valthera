"""Robotics domain action processors for Valthera."""

import logging
from typing import Any, Dict, List, Optional, Union
import torch
import torch.nn as nn
import numpy as np

from ...core.base import BaseActionProcessor
from ...core.registry import register_component

logger = logging.getLogger(__name__)


@register_component("action_processor", "delta_pose", is_default=True)
class DeltaPoseProcessor(BaseActionProcessor):
    """Delta pose processor for robot manipulation actions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.action_dim = config.get("action_dim", 7)  # 3 pos + 4 quat
        self.normalize = config.get("normalize", True)
        self.clip_actions = config.get("clip_actions", True)
        self.clip_range = config.get("clip_range", (-1.0, 1.0))
        
        # Statistics for normalization
        self.action_mean = None
        self.action_std = None
        
        # Simple MLP encoder for actions
        self.encoder = nn.Sequential(
            nn.Linear(self.action_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.action_dim),
            nn.Tanh()  # Output in [-1, 1] range
        )
    
    def fit(self, actions: Union[List, np.ndarray, torch.Tensor]) -> "DeltaPoseProcessor":
        """Fit the processor to the action data."""
        # Convert actions to numpy array
        if isinstance(actions, list):
            action_arrays = []
            for action in actions:
                if isinstance(action, (list, np.ndarray)):
                    action_arrays.append(np.array(action))
                else:
                    # Handle other types
                    action_arrays.append(np.array([action]))
            actions_array = np.array(action_arrays)
        elif isinstance(actions, torch.Tensor):
            actions_array = actions.numpy()
        else:
            actions_array = np.array(actions)
        
        # Ensure 2D array
        if actions_array.ndim == 1:
            actions_array = actions_array.reshape(1, -1)
        
        # Compute statistics for normalization
        if self.normalize:
            self.action_mean = np.mean(actions_array, axis=0)
            self.action_std = np.std(actions_array, axis=0)
            # Avoid division by zero
            self.action_std = np.where(self.action_std == 0, 1.0, self.action_std)
            
            logger.info(f"Action statistics - Mean: {self.action_mean}, Std: {self.action_std}")
        
        self._is_fitted = True
        return self
    
    def transform(self, actions: Union[List, np.ndarray, torch.Tensor]) -> torch.Tensor:
        """Transform actions to the format expected by the model."""
        if not self._is_fitted:
            raise ValueError("Processor not fitted. Call fit() first.")
        
        # Convert to numpy array
        if isinstance(actions, list):
            action_arrays = []
            for action in actions:
                if isinstance(action, (list, np.ndarray)):
                    action_arrays.append(np.array(action))
                else:
                    action_arrays.append(np.array([action]))
            actions_array = np.array(action_arrays)
        elif isinstance(actions, torch.Tensor):
            actions_array = actions.numpy()
        else:
            actions_array = np.array(actions)
        
        # Ensure 2D array
        if actions_array.ndim == 1:
            actions_array = actions_array.reshape(1, -1)
        
        # Normalize if enabled
        if self.normalize and self.action_mean is not None:
            actions_array = (actions_array - self.action_mean) / self.action_std
        
        # Clip actions if enabled
        if self.clip_actions:
            actions_array = np.clip(actions_array, self.clip_range[0], self.clip_range[1])
        
        # Convert to tensor
        actions_tensor = torch.tensor(actions_array, dtype=torch.float32)
        
        # Encode through action network
        with torch.no_grad():
            encoded_actions = self.encoder(actions_tensor)
        
        return encoded_actions
    
    def inverse_transform(self, processed_actions: torch.Tensor) -> Union[np.ndarray, torch.Tensor]:
        """Inverse transform processed actions back to original format."""
        # This is a simplified inverse transform
        # In practice, you would decode through the encoder and denormalize
        
        # For now, just return the processed actions
        if isinstance(processed_actions, torch.Tensor):
            return processed_actions
        else:
            return torch.tensor(processed_actions, dtype=torch.float32)
    
    def get_action_space_info(self) -> Dict[str, Any]:
        """Get information about the action space."""
        return {
            "action_dim": self.action_dim,
            "action_mean": self.action_mean.tolist() if self.action_mean is not None else None,
            "action_std": self.action_std.tolist() if self.action_std is not None else None,
            "normalize": self.normalize,
            "clip_actions": self.clip_actions,
            "clip_range": self.clip_range
        }


@register_component("action_processor", "joint_control")
class JointControlProcessor(BaseActionProcessor):
    """Joint control processor for robot joint actions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.num_joints = config.get("num_joints", 7)
        self.joint_limits = config.get("joint_limits", None)
        self.normalize = config.get("normalize", True)
        self.clip_actions = config.get("clip_actions", True)
        
        # Statistics for normalization
        self.joint_mean = None
        self.joint_std = None
        
        # Simple MLP encoder for joint actions
        self.encoder = nn.Sequential(
            nn.Linear(self.num_joints, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.num_joints),
            nn.Tanh()  # Output in [-1, 1] range
        )
    
    def fit(self, actions: Union[List, np.ndarray, torch.Tensor]) -> "JointControlProcessor":
        """Fit the processor to the action data."""
        # Convert actions to numpy array
        if isinstance(actions, list):
            action_arrays = []
            for action in actions:
                if isinstance(action, (list, np.ndarray)):
                    action_arrays.append(np.array(action))
                else:
                    action_arrays.append(np.array([action]))
            actions_array = np.array(action_arrays)
        elif isinstance(actions, torch.Tensor):
            actions_array = actions.numpy()
        else:
            actions_array = np.array(actions)
        
        # Ensure 2D array
        if actions_array.ndim == 1:
            actions_array = actions_array.reshape(1, -1)
        
        # Validate joint dimensions
        if actions_array.shape[1] != self.num_joints:
            logger.warning(f"Expected {self.num_joints} joints, got {actions_array.shape[1]}")
            # Adjust to match expected dimensions
            if actions_array.shape[1] < self.num_joints:
                # Pad with zeros
                padding = np.zeros((actions_array.shape[0], self.num_joints - actions_array.shape[1]))
                actions_array = np.hstack([actions_array, padding])
            else:
                # Truncate
                actions_array = actions_array[:, :self.num_joints]
        
        # Compute statistics for normalization
        if self.normalize:
            self.joint_mean = np.mean(actions_array, axis=0)
            self.joint_std = np.std(actions_array, axis=0)
            # Avoid division by zero
            self.joint_std = np.where(self.joint_std == 0, 1.0, self.joint_std)
            
            logger.info(f"Joint action statistics - Mean: {self.joint_mean}, Std: {self.joint_std}")
        
        self._is_fitted = True
        return self
    
    def transform(self, actions: Union[List, np.ndarray, torch.Tensor]) -> torch.Tensor:
        """Transform actions to the format expected by the model."""
        if not self._is_fitted:
            raise ValueError("Processor not fitted. Call fit() first.")
        
        # Convert to numpy array
        if isinstance(actions, list):
            action_arrays = []
            for action in actions:
                if isinstance(action, (list, np.ndarray)):
                    action_arrays.append(np.array(action))
                else:
                    action_arrays.append(np.array([action]))
            actions_array = np.array(action_arrays)
        elif isinstance(actions, torch.Tensor):
            actions_array = actions.numpy()
        else:
            actions_array = np.array(actions)
        
        # Ensure 2D array
        if actions_array.ndim == 1:
            actions_array = actions_array.reshape(1, -1)
        
        # Validate and adjust dimensions
        if actions_array.shape[1] != self.num_joints:
            if actions_array.shape[1] < self.num_joints:
                # Pad with zeros
                padding = np.zeros((actions_array.shape[0], self.num_joints - actions_array.shape[1]))
                actions_array = np.hstack([actions_array, padding])
            else:
                # Truncate
                actions_array = actions_array[:, :self.num_joints]
        
        # Normalize if enabled
        if self.normalize and self.joint_mean is not None:
            actions_array = (actions_array - self.joint_mean) / self.joint_std
        
        # Apply joint limits if specified
        if self.joint_limits is not None:
            actions_array = np.clip(actions_array, self.joint_limits[0], self.joint_limits[1])
        
        # Convert to tensor
        actions_tensor = torch.tensor(actions_array, dtype=torch.float32)
        
        # Encode through action network
        with torch.no_grad():
            encoded_actions = self.encoder(actions_tensor)
        
        return encoded_actions
    
    def inverse_transform(self, processed_actions: torch.Tensor) -> Union[np.ndarray, torch.Tensor]:
        """Inverse transform processed actions back to original format."""
        # This is a simplified inverse transform
        if isinstance(processed_actions, torch.Tensor):
            return processed_actions
        else:
            return torch.tensor(processed_actions, dtype=torch.float32)
    
    def get_joint_info(self) -> Dict[str, Any]:
        """Get information about the joint configuration."""
        return {
            "num_joints": self.num_joints,
            "joint_limits": self.joint_limits,
            "joint_mean": self.joint_mean.tolist() if self.joint_mean is not None else None,
            "joint_std": self.joint_std.tolist() if self.joint_std is not None else None,
            "normalize": self.normalize,
            "clip_actions": self.clip_actions
        }
