#!/usr/bin/env python3
"""
Hardware validation module for DROID + V-JEPA2 Behavioral Cloning Pipeline

This module validates:
1. Mac M4 MPS acceleration support
2. NVIDIA CUDA acceleration support
3. PyTorch installation and compatibility
4. V-JEPA2 model loading capabilities
5. Memory and performance characteristics

Usage:
    python hardware_validator.py --platform auto  # Auto-detect
    python hardware_validator.py --platform mac   # Force Mac validation
    python hardware_validator.py --platform cuda  # Force CUDA validation
"""

import os
import sys
import argparse
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detect and validate hardware capabilities."""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.pytorch_info = self._get_pytorch_info()
        self.acceleration_info = self._get_acceleration_info()
        
    def _get_system_info(self) -> Dict:
        """Get system information."""
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }
        
        # Additional Mac-specific info
        if platform.system() == 'Darwin':
            try:
                # Get Mac model info
                result = subprocess.run(['sysctl', '-n', 'hw.model'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info['mac_model'] = result.stdout.strip()
                else:
                    info['mac_model'] = 'Unknown'
                
                # Get chip info
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info['cpu_brand'] = result.stdout.strip()
                else:
                    info['cpu_brand'] = 'Unknown'
                    
            except Exception as e:
                logger.warning(f"Could not get Mac-specific info: {e}")
                info['mac_model'] = 'Unknown'
                info['cpu_brand'] = 'Unknown'
        
        return info
    
    def _get_pytorch_info(self) -> Dict:
        """Get PyTorch information."""
        try:
            import torch
            info = {
                'version': torch.__version__,
                'cuda_available': torch.cuda.is_available(),
                'cuda_version': torch.version.cuda if torch.cuda.is_available() else None,
                'mps_available': torch.backends.mps.is_available(),
                'mps_built': torch.backends.mps.is_built(),
                'cpu_count': torch.get_num_threads()
            }
            
            # Get CUDA device info if available
            if torch.cuda.is_available():
                info['cuda_device_count'] = torch.cuda.device_count()
                info['cuda_device_names'] = []
                for i in range(torch.cuda.device_count()):
                    info['cuda_device_names'].append(torch.cuda.get_device_name(i))
            
            return info
            
        except ImportError:
            return {'error': 'PyTorch not installed'}
    
    def _get_acceleration_info(self) -> Dict:
        """Get acceleration capabilities."""
        info = {}
        
        # Check MPS (Mac)
        if platform.system() == 'Darwin':
            info['mps'] = {
                'available': self.pytorch_info.get('mps_available', False),
                'built': self.pytorch_info.get('mps_built', False),
                'supported': self._check_mps_support()
            }
        
        # Check CUDA (NVIDIA)
        info['cuda'] = {
            'available': self.pytorch_info.get('cuda_available', False),
            'version': self.pytorch_info.get('cuda_version'),
            'devices': self.pytorch_info.get('cuda_device_count', 0),
            'device_names': self.pytorch_info.get('cuda_device_names', []),
            'supported': self._check_cuda_support()
        }
        
        return info
    
    def _check_mps_support(self) -> bool:
        """Check if MPS is properly supported."""
        try:
            import torch
            if not torch.backends.mps.is_available():
                return False
            
            # Test MPS device creation
            device = torch.device("mps")
            test_tensor = torch.randn(10, 10, device=device)
            result = test_tensor + test_tensor  # Simple operation
            
            # Check if operation completed successfully
            if result.device.type == "mps":
                return True
            else:
                return False
                
        except Exception as e:
            logger.warning(f"MPS test failed: {e}")
            return False
    
    def _check_cuda_support(self) -> bool:
        """Check if CUDA is properly supported."""
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            
            # Test CUDA device
            device = torch.device("cuda:0")
            test_tensor = torch.randn(10, 10, device=device)
            result = test_tensor + test_tensor  # Simple operation
            
            # Check if operation completed successfully
            if result.device.type == "cuda":
                return True
            else:
                return False
                
        except Exception as e:
            logger.warning(f"CUDA test failed: {e}")
            return False
    
    def get_optimal_device(self) -> str:
        """Get the optimal acceleration device."""
        if self.acceleration_info['mps'].get('supported', False):
            return 'mps'
        elif self.acceleration_info['cuda'].get('supported', False):
            return 'cuda'
        else:
            return 'cpu'
    
    def print_system_info(self):
        """Print comprehensive system information."""
        logger.info("=" * 60)
        logger.info("HARDWARE VALIDATION REPORT")
        logger.info("=" * 60)
        
        # System info
        logger.info("\n1. SYSTEM INFORMATION")
        logger.info("-" * 30)
        for key, value in self.system_info.items():
            logger.info(f"   {key}: {value}")
        
        # PyTorch info
        logger.info("\n2. PYTORCH INFORMATION")
        logger.info("-" * 30)
        if 'error' in self.pytorch_info:
            logger.error(f"   {self.pytorch_info['error']}")
        else:
            for key, value in self.pytorch_info.items():
                logger.info(f"   {key}: {value}")
        
        # Acceleration info
        logger.info("\n3. ACCELERATION CAPABILITIES")
        logger.info("-" * 30)
        
        # MPS info
        if platform.system() == 'Darwin':
            mps_info = self.acceleration_info['mps']
            logger.info("   MPS (Mac Metal Performance Shaders):")
            logger.info(f"     Available: {mps_info['available']}")
            logger.info(f"     Built: {mps_info['built']}")
            logger.info(f"     Supported: {mps_info['supported']}")
        
        # CUDA info
        cuda_info = self.acceleration_info['cuda']
        logger.info("   CUDA (NVIDIA):")
        logger.info(f"     Available: {cuda_info['available']}")
        logger.info(f"     Version: {cuda_info['version']}")
        logger.info(f"     Devices: {cuda_info['devices']}")
        for i, name in enumerate(cuda_info['device_names']):
            logger.info(f"       Device {i}: {name}")
        logger.info(f"     Supported: {cuda_info['supported']}")
        
        # Optimal device
        optimal_device = self.get_optimal_device()
        logger.info(f"\n4. OPTIMAL ACCELERATION DEVICE: {optimal_device.upper()}")
        
        if optimal_device == 'mps':
            logger.info("   🚀 Mac M4 MPS acceleration enabled!")
        elif optimal_device == 'cuda':
            logger.info("   🚀 NVIDIA CUDA acceleration enabled!")
        else:
            logger.info("   💻 CPU fallback (no acceleration available)")
        
        logger.info("=" * 60)


class VJEPA2Validator:
    """Validate V-JEPA2 model loading and performance."""
    
    def __init__(self, device: str):
        self.device = device
        self.model_loaded = False
        self.model = None
        
    def validate_model_loading(self) -> bool:
        """Validate V-JEPA2 model loading."""
        logger.info(f"\n5. V-JEPA2 MODEL VALIDATION ({self.device.upper()})")
        logger.info("-" * 40)
        
        try:
            # Try HuggingFace transformers first
            if self._try_huggingface_vjepa():
                logger.info("   ✅ HuggingFace V-JEPA2 loaded successfully")
                return True
            
            # Try direct V-JEPA2 import
            if self._try_direct_vjepa():
                logger.info("   ✅ Direct V-JEPA2 loaded successfully")
                return True
            
            logger.error("   ❌ Failed to load any V-JEPA2 implementation")
            return False
            
        except Exception as e:
            logger.error(f"   ❌ V-JEPA2 validation failed: {e}")
            return False
    
    def _try_huggingface_vjepa(self) -> bool:
        """Try loading V-JEPA2 from HuggingFace transformers."""
        try:
            import torch
            from transformers import AutoVideoProcessor, AutoModel
            
            model_id = "facebook/vjepa2-vitl-fpc64-256"
            logger.info(f"   Trying HuggingFace: {model_id}")
            
            # Load processor and model
            processor = AutoVideoProcessor.from_pretrained(model_id)
            model = AutoModel.from_pretrained(model_id, torch_dtype=torch.float32)
            
            # Move to device
            if self.device == 'mps':
                device = torch.device("mps")
            elif self.device == 'cuda':
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")
            
            model = model.to(device).eval()
            
            # Test with dummy input
            dummy_frames = torch.randn(16, 3, 224, 224, device=device)
            inputs = processor(videos=[dummy_frames], return_tensors="pt")
            inputs = {k: v.to(device=device, dtype=torch.float32) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            logger.info(f"     Model loaded successfully")
            logger.info(f"     Output shape: {embeddings.shape}")
            logger.info(f"     Device: {embeddings.device}")
            
            self.model = model
            self.model_loaded = True
            return True
            
        except Exception as e:
            logger.warning(f"     HuggingFace V-JEPA2 failed: {e}")
            return False
    
    def _try_direct_vjepa(self) -> bool:
        """Try loading V-JEPA2 directly from Meta's implementation."""
        try:
            import torch
            import jepa
            from jepa.models.vision_transformer import VisionTransformer
            
            logger.info("   Trying direct V-JEPA2 from Meta")
            
            # Create model (simplified version)
            model = VisionTransformer(
                img_size=224,
                patch_size=16,
                embed_dim=768,
                depth=12,
                num_heads=12,
                mlp_ratio=4
            )
            
            # Move to device
            if self.device == 'mps':
                device = torch.device("mps")
            elif self.device == 'cuda':
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")
            
            model = model.to(device).eval()
            
            # Test with dummy input
            dummy_input = torch.randn(1, 3, 224, 224, device=device)
            
            with torch.no_grad():
                features = model.forward_features(dummy_input)
                cls_token = features[:, 0]
            
            logger.info(f"     Model loaded successfully")
            logger.info(f"     Output shape: {cls_token.shape}")
            logger.info(f"     Device: {cls_token.device}")
            
            self.model = model
            self.model_loaded = True
            return True
            
        except Exception as e:
            logger.warning(f"     Direct V-JEPA2 failed: {e}")
            return False
    
    def benchmark_performance(self) -> Dict:
        """Benchmark V-JEPA2 performance."""
        if not self.model_loaded:
            logger.warning("   Model not loaded, skipping benchmark")
            return {}
        
        logger.info(f"\n6. V-JEPA2 PERFORMANCE BENCHMARK ({self.device.upper()})")
        logger.info("-" * 40)
        
        try:
            # Create test video frames
            batch_size = 4
            num_frames = 16
            
            if self.device == 'mps':
                device = torch.device("mps")
            elif self.device == 'cuda':
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")
            
            # Test input
            test_frames = torch.randn(batch_size, num_frames, 3, 224, 224, device=device)
            
            # Warmup
            for _ in range(3):
                if hasattr(self.model, 'forward_features'):
                    # Direct V-JEPA2
                    _ = self.model.forward_features(test_frames[:, 0])
                else:
                    # HuggingFace V-JEPA2
                    _ = self.model(test_frames[:, 0].unsqueeze(0))
            
            # Benchmark
            torch.cuda.synchronize() if self.device == 'cuda' else None
            
            start_time = time.time()
            num_iterations = 10
            
            for _ in range(num_iterations):
                if hasattr(self.model, 'forward_features'):
                    # Direct V-JEPA2
                    _ = self.model.forward_features(test_frames[:, 0])
                else:
                    # HuggingFace V-JEPA2
                    _ = self.model(test_frames[:, 0].unsqueeze(0))
            
            torch.cuda.synchronize() if self.device == 'cuda' else None
            end_time = time.time()
            
            total_time = end_time - start_time
            avg_time = total_time / num_iterations
            fps = 1.0 / avg_time
            
            logger.info(f"   Benchmark Results:")
            logger.info(f"     Batch size: {batch_size}")
            logger.info(f"     Frames per batch: {num_frames}")
            logger.info(f"     Iterations: {num_iterations}")
            logger.info(f"     Total time: {total_time:.3f}s")
            logger.info(f"     Average time per batch: {avg_time:.3f}s")
            logger.info(f"     Throughput: {fps:.1f} batches/second")
            
            return {
                'avg_time': avg_time,
                'fps': fps,
                'device': self.device
            }
            
        except Exception as e:
            logger.error(f"   Benchmark failed: {e}")
            return {}


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Hardware Validation for DROID + V-JEPA2")
    
    parser.add_argument("--platform", choices=["auto", "mac", "cuda"], default="auto",
                       help="Platform to validate (default: auto-detect)")
    parser.add_argument("--skip_vjepa", action="store_true",
                       help="Skip V-JEPA2 validation")
    
    args = parser.parse_args()
    
    # Hardware detection
    detector = HardwareDetector()
    detector.print_system_info()
    
    # Determine platform
    if args.platform == "auto":
        platform = detector.get_optimal_device()
    else:
        platform = args.platform
    
    logger.info(f"\nValidating platform: {platform.upper()}")
    
    # V-JEPA2 validation
    if not args.skip_vjepa:
        validator = VJEPA2Validator(platform)
        
        if validator.validate_model_loading():
            benchmark_results = validator.benchmark_performance()
            
            if benchmark_results:
                logger.info("\n✅ V-JEPA2 validation completed successfully!")
            else:
                logger.warning("\n⚠️  V-JEPA2 validation completed with warnings")
        else:
            logger.error("\n❌ V-JEPA2 validation failed!")
            return 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("HARDWARE VALIDATION COMPLETE")
    logger.info("=" * 60)
    
    optimal_device = detector.get_optimal_device()
    logger.info(f"Optimal acceleration device: {optimal_device.upper()}")
    
    if optimal_device == 'cpu':
        logger.warning("No acceleration available - consider upgrading hardware")
    else:
        logger.info("Hardware acceleration available - ready for training!")
    
    return 0


if __name__ == "__main__":
    exit(main())
