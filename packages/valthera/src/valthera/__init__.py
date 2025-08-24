"""Valthera: Universal Behavioral Cloning Library.

A domain-agnostic library for learning from expert demonstrations across
multiple domains including robotics, finance, gaming, and autonomous driving.
"""

from .core.bc import BC
from .core.registry import Registry
from .core.base import BaseObservationProcessor, BaseActionProcessor, BasePolicy

# Import new components for behavioral cloning
try:
    from .models.components.vision_encoder import VisionEncoder
    from .models.components.policy_network import PolicyNetwork, GRUPolicy, LSTMPolicy
    from .models.components.behavioral_cloning import BehavioralCloningModel
    from .training.behavioral_cloning import BehavioralCloningTrainer
except ImportError:
    # Components might not be available in all installations
    pass

__version__ = "0.1.0"
__all__ = [
    "BC", 
    "Registry", 
    "BaseObservationProcessor", 
    "BaseActionProcessor", 
    "BasePolicy",
    # New components (if available)
    "VisionEncoder",
    "PolicyNetwork", 
    "GRUPolicy",
    "LSTMPolicy",
    "BehavioralCloningModel",
    "BehavioralCloningTrainer"
]
