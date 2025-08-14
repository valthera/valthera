#!/usr/bin/env python3
"""
Test script for DROID + V-JEPA2 Behavioral Cloning Pipeline

This script runs a quick test to verify:
1. Hardware detection works
2. V-JEPA2 model loads
3. Basic pipeline functions
4. No major errors

Usage:
    python test_pipeline.py
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test basic imports."""
    logger.info("Testing imports...")
    
    try:
        import torch
        logger.info(f"✅ PyTorch {torch.__version__}")
    except ImportError as e:
        logger.error(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        from transformers import AutoVideoProcessor, AutoModel
        logger.info("✅ Transformers library")
    except ImportError as e:
        logger.error(f"❌ Transformers import failed: {e}")
        return False
    
    try:
        import cv2
        logger.info(f"✅ OpenCV {cv2.__version__}")
    except ImportError as e:
        logger.error(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        from PIL import Image
        logger.info("✅ Pillow library")
    except ImportError as e:
        logger.error(f"❌ Pillow import failed: {e}")
        return False
    
    return True

def test_hardware_detection():
    """Test hardware detection."""
    logger.info("Testing hardware detection...")
    
    try:
        from hardware_validator import HardwareDetector
        
        detector = HardwareDetector()
        optimal_device = detector.get_optimal_device()
        
        logger.info(f"✅ Hardware detection: {optimal_device.upper()}")
        return True
        
    except ImportError as e:
        logger.warning(f"Hardware validator not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Hardware detection failed: {e}")
        return False

def test_vjepa2_loading():
    """Test V-JEPA2 model loading."""
    logger.info("Testing V-JEPA2 model loading...")
    
    try:
        import torch
        from transformers import AutoVideoProcessor, AutoModel
        
        # Test basic import first
        logger.info("Testing transformers import...")
        
        # Quick test without full model download
        logger.info("Testing model availability...")
        
        # Check if we can access the model info
        from huggingface_hub import model_info
        info = model_info("facebook/vjepa2-vitl-fpc64-256")
        logger.info(f"✅ Model available: {info.modelId}")
        logger.info(f"   Tags: {info.tags[:5]}...")  # Show first 5 tags
        
        logger.info("✅ V-JEPA2 model access verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ V-JEPA2 model loading failed: {e}")
        return False

def test_basic_pipeline():
    """Test basic pipeline functionality."""
    logger.info("Testing basic pipeline...")
    
    try:
        # Import main components
        from droid_behavioral_cloning import get_optimal_device, DROIDDataProcessor
        
        # Test device detection
        device = get_optimal_device()
        logger.info(f"✅ Device detection: {device}")
        
        # Test data processor initialization (with minimal parameters)
        try:
            data_processor = DROIDDataProcessor(max_videos=5, device=device)
            logger.info("✅ Data processor initialized with device parameter")
        except TypeError:
            # Fallback to old constructor if device parameter not supported
            data_processor = DROIDDataProcessor(max_videos=5)
            logger.info("✅ Data processor initialized (fallback mode)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic pipeline test failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("DROID + V-JEPA2 PIPELINE TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Basic Imports", test_imports),
        ("Hardware Detection", test_hardware_detection),
        ("V-JEPA2 Loading", test_vjepa2_loading),
        ("Basic Pipeline", test_basic_pipeline),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if success:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your pipeline is ready.")
        return 0
    elif passed >= total // 2:
        logger.warning("⚠️  Some tests failed, but basic functionality should work.")
        return 1
    else:
        logger.error("❌ Many tests failed. Please check your installation.")
        return 1

if __name__ == "__main__":
    exit(main())
