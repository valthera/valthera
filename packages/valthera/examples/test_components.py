#!/usr/bin/env python3
"""
Test script for DROID behavioral cloning components.

This script tests the individual components to ensure they work correctly.
"""

import sys
import torch
import numpy as np
from pathlib import Path

# Add the src directory to the path for imports
# Fix the path to work from the examples directory
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from valthera.models.components.vision_encoder import VisionEncoder
    from valthera.models.components.policy_network import PolicyNetwork, GRUPolicy
    from valthera.models.components.behavioral_cloning import BehavioralCloningModel
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Added to path: {src_dir}")
    print(f"Available in path: {sys.path}")
    sys.exit(1)


def test_vision_encoder():
    """Test the vision encoder component."""
    print("Testing Vision Encoder...")
    
    # Initialize encoder
    config = {
        "output_dim": 768,
        "image_size": (224, 224),
        "freeze_encoder": True
    }
    
    encoder = VisionEncoder(config)
    
    # Test with mock image
    mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Encode single image
    features = encoder.encode(mock_image)
    print(f"  Single image encoding: {features.shape}")
    
    # Encode batch of images
    mock_images = [mock_image] * 4
    batch_features = encoder.encode(mock_images)
    print(f"  Batch encoding: {batch_features.shape}")
    
    # Test freezing/unfreezing
    print(f"  Encoder frozen: {encoder.freeze_encoder}")
    encoder.unfreeze()
    print(f"  Encoder frozen after unfreeze: {encoder.freeze_encoder}")
    encoder.freeze()
    
    print("  ✅ Vision Encoder tests passed!")
    return encoder


def test_policy_network():
    """Test the policy network component."""
    print("\nTesting Policy Network...")
    
    # Test GRU policy
    gru_policy = GRUPolicy(input_dim=768, hidden_dim=256, output_dim=6)
    
    # Test forward pass
    mock_features = torch.randn(2, 32, 768)  # (batch, seq_len, features)
    output, hidden = gru_policy(mock_features)
    print(f"  GRU output shape: {output.shape}")
    print(f"  GRU hidden shape: {hidden.shape}")
    
    # Test action prediction
    action_dict = gru_policy.predict_action(mock_features)
    print(f"  Action dict keys: {list(action_dict.keys())}")
    print(f"  Pose deltas shape: {action_dict['dpose'].shape}")
    print(f"  Grip shape: {action_dict['grip'].shape}")
    
    # Test LSTM policy
    lstm_policy = PolicyNetwork({
        "input_dim": 768,
        "hidden_dim": 256,
        "output_dim": 6,
        "use_lstm": True
    })
    
    output, hidden = lstm_policy(mock_features)
    print(f"  LSTM output shape: {output.shape}")
    # LSTM returns hidden state as tuple (h_n, c_n)
    if isinstance(hidden, tuple):
        h_n, c_n = hidden
        print(f"  LSTM hidden state shape: {h_n.shape}")
        print(f"  LSTM cell state shape: {c_n.shape}")
    else:
        print(f"  LSTM hidden shape: {hidden.shape}")
    
    print("  ✅ Policy Network tests passed!")
    return gru_policy


def test_behavioral_cloning_model():
    """Test the complete behavioral cloning model."""
    print("\nTesting Behavioral Cloning Model...")
    
    # Initialize model
    config = {
        "vision": {
            "output_dim": 768,
            "image_size": (224, 224),
            "freeze_encoder": True
        },
        "policy": {
            "input_dim": 768,
            "hidden_dim": 256,
            "output_dim": 6,
            "use_lstm": False
        },
        "freeze_vision": True,
        "use_sequence": True,
        "sequence_length": 32
    }
    
    model = BehavioralCloningModel(config)
    
    # Test model info
    model_info = model.get_model_info()
    print(f"  Model info: {model_info['total_parameters']:,} total parameters")
    print(f"  Trainable: {model_info['trainable_parameters']:,} parameters")
    
    # Test forward pass with mock images
    mock_images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(32)]
    
    outputs = model(mock_images)
    print(f"  Forward pass output keys: {list(outputs.keys())}")
    print(f"  Vision features shape: {outputs['vision_features'].shape}")
    print(f"  Pose deltas shape: {outputs['dpose'].shape}")
    
    # Test action prediction from features
    mock_features = torch.randn(1, 32, 768)
    action_dict = model.predict_action(mock_features)
    print(f"  Action prediction keys: {list(action_dict.keys())}")
    
    # Test checkpointing
    checkpoint_path = "test_checkpoint.pt"
    model.save_checkpoint(checkpoint_path, test_data="test")
    
    # Load checkpoint
    new_model = BehavioralCloningModel(config)
    new_model.load_checkpoint(checkpoint_path)
    
    # Clean up
    Path(checkpoint_path).unlink(missing_ok=True)
    
    print("  ✅ Behavioral Cloning Model tests passed!")
    return model


def test_integration():
    """Test integration between components."""
    print("\nTesting Component Integration...")
    
    # Create components
    vision_encoder = VisionEncoder({"output_dim": 768})
    policy_network = PolicyNetwork({"input_dim": 768, "output_dim": 6})
    
    # Test data flow
    mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Encode image
    features = vision_encoder.encode(mock_image)
    print(f"  Image encoding: {features.shape}")
    
    # Predict action - ensure correct dimensions: (batch_size, seq_len, input_dim)
    features_tensor = features.unsqueeze(1)  # Add sequence dimension: (batch_size, 1, input_dim)
    action_dict = policy_network.predict_action(features_tensor)
    print(f"  Action prediction: {action_dict['dpose'].shape}")
    
    print("  ✅ Integration tests passed!")


def main():
    """Run all tests."""
    print("Running DROID Behavioral Cloning Component Tests")
    print("=" * 50)
    
    try:
        # Test individual components
        vision_encoder = test_vision_encoder()
        policy_network = test_policy_network()
        bc_model = test_behavioral_cloning_model()
        
        # Test integration
        test_integration()
        
        print("\n🎉 All tests passed successfully!")
        print("\nComponents are ready for use in the DROID behavioral cloning example.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
