# DROID + V-JEPA2 Behavioral Cloning Setup Guide

This guide helps you set up the DROID behavioral cloning pipeline with real V-JEPA2 embeddings on your hardware.

## 🚀 Quick Start

### 1. Automatic Setup (Recommended)
```bash
# Auto-detect your platform and install dependencies
python setup_environment.py --auto
```

### 2. Platform-Specific Setup
```bash
# For Mac M4 with MPS acceleration
python setup_environment.py --mac

# For NVIDIA with CUDA acceleration  
python setup_environment.py --cuda

# For CPU-only systems
python setup_environment.py --cpu
```

## 🔧 Hardware Requirements

### Mac M4 (M1/M2/M3/M4) with MPS
- **OS**: macOS 12.3+ (Monterey or later)
- **Chip**: Apple Silicon (M1, M1 Pro, M1 Max, M2, M2 Pro, M2 Max, M3, M3 Pro, M3 Max, M4)
- **Memory**: 8GB+ RAM recommended
- **Storage**: 10GB+ free space for models and datasets

### NVIDIA with CUDA
- **OS**: Linux (Ubuntu 18.04+ recommended) or Windows 10/11
- **GPU**: NVIDIA GPU with CUDA support (RTX 20/30/40 series recommended)
- **CUDA**: Version 11.8 or 12.1
- **Memory**: 8GB+ VRAM recommended
- **Storage**: 10GB+ free space for models and datasets

### CPU-Only
- **OS**: Any platform with Python 3.8+
- **CPU**: Multi-core processor (4+ cores recommended)
- **Memory**: 16GB+ RAM recommended
- **Storage**: 10GB+ free space for models and datasets

## 📦 Installation Steps

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd packages/valthera/examples
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Run Automatic Setup
```bash
python setup_environment.py --auto
```

This script will:
- Detect your hardware platform
- Install the appropriate PyTorch version
- Install V-JEPA2 dependencies
- Validate the installation

## 🔍 Manual Installation

If you prefer manual installation, follow these steps:

### For Mac M4 (MPS)
```bash
# Install PyTorch with MPS support
pip install torch torchvision torchaudio

# Install other dependencies
pip install -r requirements-mac-m4.txt
```

### For NVIDIA (CUDA)
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -r requirements-cuda.txt
```

### For CPU-Only
```bash
# Install PyTorch CPU-only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install -r requirements-cpu.txt
```

## ✅ Validation

### 1. Hardware Validation
```bash
# Run comprehensive hardware validation
python hardware_validator.py --platform auto

# Test specific platform
python hardware_validator.py --platform mac    # Mac M4
python hardware_validator.py --platform cuda   # NVIDIA CUDA
```

### 2. Installation Validation
```bash
# Validate PyTorch installation
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'MPS: {torch.backends.mps.is_available()}'); print(f'CUDA: {torch.cuda.is_available()}')"

# Validate V-JEPA2 dependencies
python -c "from transformers import AutoVideoProcessor, AutoModel; print('Transformers OK')"
python -c "import cv2; print(f'OpenCV {cv2.__version__} OK')"
python -c "from PIL import Image; print('Pillow OK')"
```

## 🚀 Running the Pipeline

### 1. Quick Test
```bash
# Run with minimal data for testing
python droid_behavioral_cloning.py --num_videos 10 --epochs 5
```

### 2. Full Training
```bash
# Run full training
python droid_behavioral_cloning.py --num_videos 100 --epochs 50 --batch_size 32
```

### 3. Custom Configuration
```bash
python droid_behavioral_cloning.py \
    --num_videos 200 \
    --epochs 100 \
    --batch_size 64 \
    --learning_rate 5e-5 \
    --sequence_length 64
```

## 🐛 Troubleshooting

### Common Issues

#### 1. PyTorch Installation Fails
```bash
# Clear pip cache
pip cache purge

# Try alternative installation
pip install torch torchvision torchaudio --no-cache-dir
```

#### 2. MPS Not Available (Mac)
- Ensure macOS 12.3+ (Monterey or later)
- Check if you have Apple Silicon chip
- Try reinstalling PyTorch: `pip install --force-reinstall torch torchvision torchaudio`

#### 3. CUDA Not Available (NVIDIA)
- Check NVIDIA drivers: `nvidia-smi`
- Verify CUDA installation: `nvcc --version`
- Install correct PyTorch version for your CUDA version

#### 4. V-JEPA2 Model Loading Fails
```bash
# Check internet connection
# Try downloading manually
python -c "from transformers import AutoVideoProcessor; AutoVideoProcessor.from_pretrained('facebook/vjepa2-vitl-fpc64-256')"
```

#### 5. Out of Memory
- Reduce batch size: `--batch_size 8`
- Reduce sequence length: `--sequence_length 16`
- Use CPU fallback: `--platform cpu`

### Performance Optimization

#### Mac M4 (MPS)
- Use batch sizes of 16-32 for optimal MPS performance
- Enable Metal Performance Shaders in System Preferences
- Close other GPU-intensive applications

#### NVIDIA (CUDA)
- Use batch sizes of 32-64 for optimal CUDA performance
- Monitor GPU memory: `nvidia-smi -l 1`
- Use mixed precision training if available

#### CPU-Only
- Use smaller batch sizes (8-16)
- Enable multi-threading: `export OMP_NUM_THREADS=8`
- Consider using fewer epochs for faster iteration

## 📊 Expected Performance

### Mac M4 (MPS)
- **Training speed**: 2-5x faster than CPU
- **Memory usage**: 4-8GB RAM
- **Batch size**: 16-32 optimal

### NVIDIA (CUDA)
- **Training speed**: 5-20x faster than CPU
- **Memory usage**: 6-12GB VRAM
- **Batch size**: 32-128 optimal

### CPU-Only
- **Training speed**: Baseline
- **Memory usage**: 8-16GB RAM
- **Batch size**: 8-16 optimal

## 🔄 Updating

### Update Dependencies
```bash
# Update PyTorch
pip install --upgrade torch torchvision torchaudio

# Update other packages
pip install --upgrade transformers opencv-python pillow
```

### Update Models
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/

# Re-run setup to download latest models
python setup_environment.py --auto
```

## 📚 Additional Resources

### Documentation
- [PyTorch MPS Guide](https://pytorch.org/docs/stable/notes/mps.html)
- [PyTorch CUDA Guide](https://pytorch.org/docs/stable/notes/cuda.html)
- [V-JEPA2 Paper](https://arxiv.org/abs/2401.10104)
- [DROID Dataset](https://droid-dataset.github.io/)

### Community Support
- [PyTorch Forums](https://discuss.pytorch.org/)
- [HuggingFace Forums](https://discuss.huggingface.co/)
- [GitHub Issues](https://github.com/your-repo/issues)

## 🎯 Next Steps

After successful setup:

1. **Validate hardware**: `python hardware_validator.py`
2. **Test pipeline**: `python droid_behavioral_cloning.py --num_videos 10`
3. **Download DROID data**: The pipeline will automatically download sample data
4. **Train model**: Adjust parameters and run full training
5. **Deploy**: Use trained model for inference

## 📝 License

This setup guide is part of the Valthera project. See the main repository for license information.
