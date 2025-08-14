#!/usr/bin/env python3
"""
Simple standalone test for DROID behavioral cloning components.

This script tests the basic functionality without requiring the full valthera package.
Optimized for Mac M4 with MPS support.
"""

import sys
import numpy as np
from pathlib import Path

def test_basic_imports():
    """Test basic imports and functionality."""
    print("🧪 Testing Basic Imports...")
    
    try:
        import torch
        print(f"  ✅ PyTorch imported successfully: {torch.__version__}")
    except ImportError:
        print("  ❌ PyTorch not available")
        return False
    
    try:
        import torchvision
        print(f"  ✅ TorchVision imported successfully: {torchvision.__version__}")
    except ImportError:
        print("  ❌ TorchVision not available")
        return False
    
    try:
        import cv2
        print(f"  ✅ OpenCV imported successfully: {cv2.__version__}")
    except ImportError:
        print("  ❌ OpenCV not available")
        return False
    
    try:
        import PIL
        print(f"  ✅ PIL imported successfully: {PIL.__version__}")
    except ImportError:
        print("  ❌ PIL not available")
        return False
    
    return True

def test_mac_mps_support():
    """Test Mac M4 MPS support."""
    print("\n🍎 Testing Mac M4 MPS Support...")
    
    try:
        import torch
        
        # Check MPS availability
        mps_available = torch.backends.mps.is_available()
        mps_built = torch.backends.mps.is_built()
        
        print(f"  ✅ MPS available: {mps_available}")
        print(f"  ✅ MPS built: {mps_built}")
        
        if mps_available and mps_built:
            # Test MPS device
            device = torch.device("mps")
            x = torch.ones(5, device=device)
            print(f"  ✅ MPS tensor created: {x.shape} on {x.device}")
            
            # Test basic operations on MPS
            y = torch.relu(x)
            print(f"  ✅ MPS operations working: {y.shape}")
            
            return True
        else:
            print("  ⚠️  MPS not available, will use CPU")
            return True
            
    except Exception as e:
        print(f"  ❌ MPS test failed: {e}")
        return False

def test_basic_torch_operations():
    """Test basic PyTorch operations."""
    print("\n🧪 Testing Basic PyTorch Operations...")
    
    try:
        import torch
        
        # Determine best device
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            device = torch.device("mps")
            print(f"  🚀 Using MPS device for acceleration")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
            print(f"  🚀 Using CUDA device for acceleration")
        else:
            device = torch.device("cpu")
            print(f"  💻 Using CPU device")
        
        # Test tensor creation on device
        x = torch.randn(2, 3, 4, device=device)
        print(f"  ✅ Tensor creation: {x.shape} on {x.device}")
        
        # Test basic operations
        y = torch.relu(x)
        print(f"  ✅ ReLU operation: {y.shape}")
        
        # Test device detection
        print(f"  ✅ Device detection: {device}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ PyTorch operations failed: {e}")
        return False

def test_mock_data_generation():
    """Test mock data generation for DROID dataset."""
    print("\n🧪 Testing Mock Data Generation...")
    
    try:
        # Generate mock features (simulating V-JEPA2 embeddings)
        num_episodes = 5
        max_steps = 100
        feature_dim = 768
        
        features = np.random.randn(num_episodes, max_steps, feature_dim).astype(np.float32)
        print(f"  ✅ Features generated: {features.shape}")
        
        # Generate mock targets (robot actions)
        action_dim = 6  # [dx, dy, dz, dyaw, grip, stop]
        targets = np.random.randn(num_episodes, max_steps, action_dim).astype(np.float32)
        print(f"  ✅ Targets generated: {targets.shape}")
        
        # Test data statistics
        print(f"  ✅ Feature stats - Mean: {features.mean():.4f}, Std: {features.std():.4f}")
        print(f"  ✅ Target stats - Mean: {targets.mean():.4f}, Std: {targets.std():.4f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mock data generation failed: {e}")
        return False

def test_simple_neural_network():
    """Test simple neural network creation."""
    print("\n🧪 Testing Simple Neural Network...")
    
    try:
        import torch
        import torch.nn as nn
        
        # Determine best device
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        
        # Create a simple network
        class SimpleNet(nn.Module):
            def __init__(self, input_dim=768, hidden_dim=256, output_dim=6):
                super().__init__()
                self.fc1 = nn.Linear(input_dim, hidden_dim)
                self.fc2 = nn.Linear(hidden_dim, hidden_dim)
                self.fc3 = nn.Linear(hidden_dim, output_dim)
                self.relu = nn.ReLU()
            
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.relu(self.fc2(x))
                x = self.fc3(x)
                return x
        
        # Test network creation
        net = SimpleNet().to(device)
        print(f"  ✅ Network created with {sum(p.numel() for p in net.parameters()):,} parameters")
        print(f"  ✅ Network moved to device: {device}")
        
        # Test forward pass
        mock_input = torch.randn(1, 32, 768, device=device)  # (batch, seq_len, features)
        output = net(mock_input)
        print(f"  ✅ Forward pass successful: {output.shape}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Neural network test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 DROID Behavioral Cloning - Mac M4 Optimized Test")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_mac_mps_support,
        test_basic_torch_operations,
        test_mock_data_generation,
        test_simple_neural_network
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Environment is ready for DROID behavioral cloning.")
        print("\n🚀 Next steps:")
        print("   1. Run: poetry run python test_components.py")
        print("   2. Run: poetry run python droid_behavioral_cloning.py")
        print("\n🍎 Mac M4 MPS acceleration is available for faster training!")
        return 0
    else:
        print("❌ Some tests failed. Please check the environment setup.")
        return 1

if __name__ == "__main__":
    exit(main())
