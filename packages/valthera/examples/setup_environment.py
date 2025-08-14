#!/usr/bin/env python3
"""
Automatic environment setup for DROID + V-JEPA2 Behavioral Cloning Pipeline

This script:
1. Detects your hardware platform (Mac M4 or NVIDIA CUDA)
2. Installs the appropriate PyTorch version
3. Installs V-JEPA2 dependencies
4. Validates the installation

Usage:
    python setup_environment.py --auto  # Auto-detect and setup
    python setup_environment.py --mac   # Force Mac M4 setup
    python setup_environment.py --cuda  # Force NVIDIA CUDA setup
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

def detect_platform():
    """Detect the current platform."""
    system = platform.system()
    machine = platform.machine()
    
    if system == "Darwin" and "arm" in machine.lower():
        return "mac_m4"
    elif system == "Linux" and "x86_64" in machine:
        # Check for NVIDIA GPU
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return "cuda"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return "cpu"
    else:
        return "cpu"

def install_pytorch(platform_type):
    """Install PyTorch for the specified platform."""
    print(f"Installing PyTorch for {platform_type}...")
    
    if platform_type == "mac_m4":
        # Install PyTorch with MPS support
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio"
        ]
    elif platform_type == "cuda":
        # Install PyTorch with CUDA support
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ]
    else:
        # Install CPU-only PyTorch
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ PyTorch installed successfully for {platform_type}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PyTorch: {e}")
        return False

def install_requirements(platform_type):
    """Install platform-specific requirements."""
    print(f"Installing requirements for {platform_type}...")
    
    # Base requirements file
    base_req_file = "requirements-base.txt"
    
    # Platform-specific requirements file
    if platform_type == "mac_m4":
        req_file = "requirements-mac-m4.txt"
    elif platform_type == "cuda":
        req_file = "requirements-cuda.txt"
    else:
        req_file = "requirements-cpu.txt"
    
    # Create base requirements if it doesn't exist
    if not Path(base_req_file).exists():
        with open(base_req_file, "w") as f:
            f.write("""# Base requirements for all platforms
# Install with: pip install -r requirements-base.txt

# V-JEPA2 and video processing
transformers>=4.35.0
opencv-python>=4.8.0
pillow>=10.0.0

# Scientific computing
numpy>=1.24.0
scipy>=1.11.0

# Data handling
pandas>=2.0.0
h5py>=3.8.0

# Development and testing
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
""")
    
    # Install base requirements
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", base_req_file
        ], check=True)
        print("✅ Base requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install base requirements: {e}")
        return False
    
    # Install platform-specific requirements
    if Path(req_file).exists():
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", req_file
            ], check=True)
            print(f"✅ {platform_type} requirements installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {platform_type} requirements: {e}")
            return False
    
    return True

def validate_installation(platform_type):
    """Validate the installation."""
    print(f"Validating installation for {platform_type}...")
    
    try:
        # Test PyTorch import
        import torch
        print(f"✅ PyTorch {torch.__version__} imported successfully")
        
        # Test device availability
        if platform_type == "mac_m4":
            if torch.backends.mps.is_available():
                print("✅ MPS (Metal Performance Shaders) available")
                device = torch.device("mps")
                test_tensor = torch.randn(10, 10, device=device)
                print("✅ MPS device test passed")
            else:
                print("❌ MPS not available")
                return False
        elif platform_type == "cuda":
            if torch.cuda.is_available():
                print(f"✅ CUDA {torch.version.cuda} available")
                print(f"   Devices: {torch.cuda.device_count()}")
                for i in range(torch.cuda.device_count()):
                    print(f"   Device {i}: {torch.cuda.get_device_name(i)}")
                device = torch.device("cuda:0")
                test_tensor = torch.randn(10, 10, device=device)
                print("✅ CUDA device test passed")
            else:
                print("❌ CUDA not available")
                return False
        else:
            device = torch.device("cpu")
            test_tensor = torch.randn(10, 10, device=device)
            print("✅ CPU device test passed")
        
        # Test V-JEPA2 dependencies
        try:
            from transformers import AutoVideoProcessor, AutoModel
            print("✅ Transformers library imported successfully")
        except ImportError:
            print("❌ Transformers library not available")
            return False
        
        try:
            import cv2
            print(f"✅ OpenCV {cv2.__version__} imported successfully")
        except ImportError:
            print("❌ OpenCV not available")
            return False
        
        try:
            from PIL import Image
            print(f"✅ Pillow {Image.__version__} imported successfully")
        except ImportError:
            print("❌ Pillow not available")
            return False
        
        print("✅ All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup DROID + V-JEPA2 Environment")
    
    parser.add_argument("--auto", action="store_true", help="Auto-detect platform")
    parser.add_argument("--mac", action="store_true", help="Force Mac M4 setup")
    parser.add_argument("--cuda", action="store_true", help="Force NVIDIA CUDA setup")
    parser.add_argument("--cpu", action="store_true", help="Force CPU-only setup")
    parser.add_argument("--skip-validation", action="store_true", help="Skip installation validation")
    
    args = parser.parse_args()
    
    # Determine platform
    if args.mac:
        platform_type = "mac_m4"
    elif args.cuda:
        platform_type = "cuda"
    elif args.cpu:
        platform_type = "cpu"
    elif args.auto:
        platform_type = detect_platform()
    else:
        platform_type = detect_platform()
    
    print("=" * 60)
    print("DROID + V-JEPA2 ENVIRONMENT SETUP")
    print("=" * 60)
    print(f"Detected platform: {platform_type}")
    print(f"Python version: {platform.python_version()}")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    
    # Install PyTorch
    if not install_pytorch(platform_type):
        print("❌ Setup failed at PyTorch installation")
        return 1
    
    # Install requirements
    if not install_requirements(platform_type):
        print("❌ Setup failed at requirements installation")
        return 1
    
    # Validate installation
    if not args.skip_validation:
        if not validate_installation(platform_type):
            print("❌ Setup failed at validation")
            return 1
    
    print("\n" + "=" * 60)
    print("✅ ENVIRONMENT SETUP COMPLETE!")
    print("=" * 60)
    print(f"Platform: {platform_type}")
    print("Next steps:")
    print("1. Run hardware validation: python hardware_validator.py")
    print("2. Run DROID example: python droid_behavioral_cloning.py")
    
    return 0

if __name__ == "__main__":
    exit(main())
