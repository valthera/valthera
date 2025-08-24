"""Policy network component for behavioral cloning in Valthera."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, Any
import numpy as np

from ...core.base import BaseComponent


class PolicyNetwork(BaseComponent, nn.Module):
    """Policy network for behavioral cloning from vision features."""
    
    def __init__(self, config: Optional[dict] = None):
        BaseComponent.__init__(self, config)
        nn.Module.__init__(self)
        
        # Configuration
        self.input_dim = config.get("input_dim", 768)  # Vision feature dimension
        self.hidden_dim = config.get("hidden_dim", 256)
        self.num_layers = config.get("num_layers", 2)
        self.output_dim = config.get("output_dim", 6)  # [dx, dy, dz, dyaw, grip, stop]
        self.dropout = config.get("dropout", 0.1)
        self.use_lstm = config.get("use_lstm", False)
        
        # Initialize network
        self.network = self._create_network()
        self._is_initialized = True
    
    def _create_network(self) -> nn.Module:
        """Create the policy network."""
        if self.use_lstm:
            # LSTM-based policy
            network = nn.ModuleDict({
                'input_proj': nn.Linear(self.input_dim, self.hidden_dim),
                'lstm': nn.LSTM(
                    self.hidden_dim, 
                    self.hidden_dim, 
                    num_layers=self.num_layers,
                    batch_first=True,
                    dropout=self.dropout if self.num_layers > 1 else 0
                ),
                'output': nn.Linear(self.hidden_dim, self.output_dim)
            })
        else:
            # GRU-based policy (default)
            network = nn.ModuleDict({
                'input_proj': nn.Linear(self.input_dim, self.hidden_dim),
                'gru': nn.GRU(
                    self.hidden_dim, 
                    self.hidden_dim, 
                    num_layers=self.num_layers,
                    batch_first=True,
                    dropout=self.dropout if self.num_layers > 1 else 0
                ),
                'output': nn.Linear(self.hidden_dim, self.output_dim)
            })
        
        return network
    
    def forward(self, x: torch.Tensor, hidden_state: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through the policy network.
        
        Args:
            x: Input features of shape (batch_size, seq_len, input_dim)
            hidden_state: Optional hidden state for recurrent networks
            
        Returns:
            output: Policy outputs of shape (batch_size, seq_len, output_dim)
            hidden_state: Updated hidden state
        """
        if not self._is_initialized:
            raise RuntimeError("Policy network not initialized")
        
        # Input projection
        x = F.relu(self.network['input_proj'](x))
        
        # Recurrent processing
        if self.use_lstm:
            if hidden_state is not None:
                output, (h_n, c_n) = self.network['lstm'](x, hidden_state)
                new_hidden = (h_n, c_n)
            else:
                output, new_hidden = self.network['lstm'](x)
        else:
            if hidden_state is not None:
                output, new_hidden = self.network['gru'](x, hidden_state)
            else:
                output, new_hidden = self.network['gru'](x)
        
        # Output projection
        output = self.network['output'](output)
        
        return output, new_hidden
    
    def __call__(self, x: torch.Tensor, hidden_state: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Make the policy network callable like a PyTorch module."""
        return self.forward(x, hidden_state)
    
    def predict_action(self, features: torch.Tensor, hidden_state: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Predict action from features.
        
        Args:
            features: Input features of shape (batch_size, seq_len, input_dim)
            hidden_state: Optional hidden state
            
        Returns:
            action_dict: Dictionary containing action components
        """
        output, new_hidden = self.forward(features, hidden_state)
        
        # Split outputs into components
        dpose = output[..., :4]  # Pose deltas [dx, dy, dz, dyaw]
        grip = output[..., 4:5]  # Gripper state
        stop = output[..., 5:6]  # Stop signal
        
        # Apply activation functions
        grip_prob = torch.sigmoid(grip)
        stop_prob = torch.sigmoid(stop)
        
        action_dict = {
            'dpose': dpose,
            'grip': grip_prob,
            'stop': stop_prob,
            'grip_logits': grip,
            'stop_logits': stop,
            'hidden_state': new_hidden
        }
        
        return action_dict
    
    def get_action_dim(self) -> int:
        """Get the output action dimension."""
        return self.output_dim
    
    def get_hidden_dim(self) -> int:
        """Get the hidden dimension."""
        return self.hidden_dim
    
    def reset_hidden_state(self, batch_size: int = 1) -> torch.Tensor:
        """Reset hidden state for new episode."""
        if self.use_lstm:
            # LSTM has both hidden and cell state
            h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim)
            c0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim)
            return (h0, c0)
        else:
            # GRU only has hidden state
            return torch.zeros(self.num_layers, batch_size, self.hidden_dim)
    
    def parameters(self, recurse: bool = True):
        """Get parameters for the policy network (required for PyTorch compatibility)."""
        return self.network.parameters(recurse=recurse)
    
    def state_dict(self):
        """Get state dict for the policy network (required for PyTorch compatibility)."""
        return self.network.state_dict()
    
    def load_state_dict(self, state_dict):
        """Load state dict for the policy network (required for PyTorch compatibility)."""
        self.network.load_state_dict(state_dict)


class GRUPolicy(PolicyNetwork):
    """GRU-based policy network (alias for backward compatibility)."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 256, num_layers: int = 2, output_dim: int = 6):
        config = {
            "input_dim": input_dim,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "output_dim": output_dim,
            "use_lstm": False
        }
        super().__init__(config)


class LSTMPolicy(PolicyNetwork):
    """LSTM-based policy network."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 256, num_layers: int = 2, output_dim: int = 6):
        config = {
            "input_dim": input_dim,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "output_dim": output_dim,
            "use_lstm": True
        }
        super().__init__(config)
