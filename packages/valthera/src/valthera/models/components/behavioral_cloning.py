"""Behavioral cloning model for Valthera."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, Tuple, Union
import numpy as np

from ...core.base import BaseComponent
from .vision_encoder import VisionEncoder
from .policy_network import PolicyNetwork


class BehavioralCloningModel(BaseComponent, nn.Module):
    """End-to-end behavioral cloning model combining vision encoder and policy."""
    
    def __init__(self, config: Optional[dict] = None):
        BaseComponent.__init__(self, config)
        nn.Module.__init__(self)
        
        # Configuration
        self.vision_config = config.get("vision", {})
        self.policy_config = config.get("policy", {})
        self.freeze_vision = config.get("freeze_vision", True)
        self.use_sequence = config.get("use_sequence", True)
        self.sequence_length = config.get("sequence_length", 32)
        
        # Initialize components
        self.vision_encoder = VisionEncoder(self.vision_config)
        self.policy_network = PolicyNetwork(self.policy_config)
        
        # Ensure policy input dimension matches vision output
        if self.policy_config.get("input_dim") != self.vision_encoder.get_feature_dim():
            self.policy_config["input_dim"] = self.vision_encoder.get_feature_dim()
            # Recreate policy network with correct dimensions
            self.policy_network = PolicyNetwork(self.policy_config)
        
        # Freeze vision encoder if requested
        if self.freeze_vision:
            self.vision_encoder.freeze()
        
        self._is_initialized = True
    
    def forward(self, images: Union[torch.Tensor, np.ndarray, list], 
                hidden_state: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass through the complete model.
        
        Args:
            images: Input images (can be single, batch, or sequence)
            hidden_state: Optional hidden state for recurrent policy
            
        Returns:
            outputs: Dictionary containing all model outputs
        """
        if not self._is_initialized:
            raise RuntimeError("Model not initialized")
        
        # Encode images to features
        if isinstance(images, list):
            # List of images - treat as a sequence
            # Encode all images in the sequence
            features = []
            for img in images:
                feat = self.vision_encoder.encode(img)
                # Remove batch dimension if present (feat should be (1, feature_dim))
                if feat.dim() == 2 and feat.shape[0] == 1:
                    feat = feat.squeeze(0)  # Remove batch dim to get (feature_dim,)
                features.append(feat)
            # Stack to create (seq_len, feature_dim)
            features = torch.stack(features, dim=0)  # (seq_len, feature_dim)
            # Add batch dimension: (1, seq_len, feature_dim)
            features = features.unsqueeze(0)  # (1, seq_len, feature_dim)
        else:
            # Single image or batch
            features = self.vision_encoder.encode(images)
            
            # Ensure features have correct dimensions for policy network
            # Policy network expects (batch_size, seq_len, input_dim)
            if features.dim() == 2:
                # Single image or batch of images: (batch_size, feature_dim)
                # Add sequence dimension: (batch_size, 1, feature_dim)
                features = features.unsqueeze(1)
            elif features.dim() == 3:
                # Already in correct format: (batch_size, seq_len, feature_dim)
                pass
            else:
                raise ValueError(f"Unexpected features tensor shape: {features.shape}")
        
        # Get policy predictions
        action_dict = self.policy_network.predict_action(features, hidden_state)
        
        # Add vision features to outputs
        action_dict['vision_features'] = features
        
        return action_dict
    
    def encode_vision(self, images: Union[torch.Tensor, np.ndarray, list]) -> torch.Tensor:
        """Encode images to vision features."""
        return self.vision_encoder.encode(images)
    
    def predict_action(self, features: torch.Tensor, 
                      hidden_state: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Predict actions from pre-encoded features."""
        return self.policy_network.predict_action(features, hidden_state)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model components."""
        return {
            'vision_encoder': {
                'type': type(self.vision_encoder).__name__,
                'feature_dim': self.vision_encoder.get_feature_dim(),
                'frozen': self.vision_encoder.freeze_encoder,
                'parameters': sum(p.numel() for p in self.vision_encoder.parameters())
            },
            'policy_network': {
                'type': type(self.policy_network).__name__,
                'input_dim': self.policy_network.get_action_dim(),
                'hidden_dim': self.policy_network.get_hidden_dim(),
                'parameters': sum(p.numel() for p in self.policy_network.parameters())
            },
            'total_parameters': sum(p.numel() for p in self.parameters()),
            'trainable_parameters': sum(p.numel() for p in self.parameters() if p.requires_grad)
        }
    
    def unfreeze_vision(self):
        """Unfreeze the vision encoder for fine-tuning."""
        self.vision_encoder.unfreeze()
        self.freeze_vision = False
    
    def freeze_vision(self):
        """Freeze the vision encoder."""
        self.vision_encoder.freeze()
        self.freeze_vision = True
    
    def reset_policy_state(self, batch_size: int = 1) -> torch.Tensor:
        """Reset the policy network's hidden state."""
        return self.policy_network.reset_hidden_state(batch_size)
    
    def save_checkpoint(self, path: str, **kwargs):
        """Save model checkpoint."""
        checkpoint = {
            'vision_encoder_state': self.vision_encoder.state_dict(),
            'policy_network_state': self.policy_network.state_dict(),
            'vision_config': self.vision_config,
            'policy_config': self.policy_config,
            'model_config': {
                'freeze_vision': self.freeze_vision,
                'use_sequence': self.use_sequence,
                'sequence_length': self.sequence_length
            }
        }
        checkpoint.update(kwargs)
        torch.save(checkpoint, path)
    
    def load_checkpoint(self, path: str, **kwargs):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location='cpu')
        
        # Load component states
        self.vision_encoder.load_state_dict(checkpoint['vision_encoder_state'])
        self.policy_network.load_state_dict(checkpoint['policy_network_state'])
        
        # Load configurations
        self.vision_config = checkpoint.get('vision_config', self.vision_config)
        self.policy_config = checkpoint.get('policy_config', self.policy_config)
        
        # Load model config
        model_config = checkpoint.get('model_config', {})
        self.freeze_vision = model_config.get('freeze_vision', self.freeze_vision)
        self.use_sequence = model_config.get('use_sequence', self.use_sequence)
        self.sequence_length = model_config.get('sequence_length', self.sequence_length)
        
        # Apply freeze setting
        if self.freeze_vision:
            self.vision_encoder.freeze()
        else:
            self.vision_encoder.unfreeze()
        
        # Load additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_trainable_parameters(self):
        """Get trainable parameters for optimization."""
        trainable_params = []
        
        # Add policy parameters
        trainable_params.extend(self.policy_network.parameters())
        
        # Add vision parameters if not frozen
        if not self.freeze_vision:
            trainable_params.extend(self.vision_encoder.parameters())
        
        return trainable_params
    
    def get_frozen_parameters(self):
        """Get frozen parameters."""
        frozen_params = []
        
        if self.freeze_vision:
            frozen_params.extend(self.vision_encoder.parameters())
        
        return frozen_params
    
    def parameters(self, recurse: bool = True):
        """Get parameters for the behavioral cloning model (required for PyTorch compatibility)."""
        params = []
        params.extend(self.vision_encoder.parameters(recurse=recurse))
        params.extend(self.policy_network.parameters(recurse=recurse))
        return params
    
    def state_dict(self):
        """Get state dict for the behavioral cloning model (required for PyTorch compatibility)."""
        state_dict = {}
        state_dict['vision_encoder'] = self.vision_encoder.state_dict()
        state_dict['policy_network'] = self.policy_network.state_dict()
        return state_dict
    
    def load_state_dict(self, state_dict):
        """Load state dict for the behavioral cloning model (required for PyTorch compatibility)."""
        if 'vision_encoder' in state_dict:
            self.vision_encoder.load_state_dict(state_dict['vision_encoder'])
        if 'policy_network' in state_dict:
            self.policy_network.load_state_dict(state_dict['policy_network'])
