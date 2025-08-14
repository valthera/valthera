# Troubleshooting Guide for DROID Behavioral Cloning Example

This guide helps resolve common issues when running the DROID behavioral cloning example.

## 🚨 Common Issues and Solutions

### 1. **PyTorch Import Error**

**Error**: `ModuleNotFoundError: No module named 'torch'`

**Solution**:
```bash
# Navigate to the valthera package directory
cd packages/valthera

# Install PyTorch in Poetry environment
poetry add torch torchvision

# Verify installation
poetry run python -c "import torch; print(torch.__version__)"
```

### 2. **Wrong Directory Error**

**Error**: Import errors or file not found

**Solution**: Always run from the correct directory:
```bash
# Navigate to examples directory
cd packages/valthera/examples

# Run tests
poetry run python simple_test.py
poetry run python test_components.py
poetry run python droid_behavioral_cloning.py
```

### 3. **Path Import Issues**

**Error**: `ImportError: cannot import name 'VisionEncoder'`

**Solution**: The import paths have been fixed. If you still have issues:

```bash
# Check current directory
pwd

# Should show: .../packages/valthera/examples

# Check if files exist
ls -la *.py
ls -la ../src/valthera/models/components/
```

### 4. **Poetry Environment Issues**

**Error**: Poetry commands not found or environment not activated

**Solution**:
```bash
# Install Poetry if not available
curl -sSL https://install.python-poetry.org | python3 -

# Activate Poetry environment
poetry shell

# Or run with poetry run
poetry run python simple_test.py
```

### 5. **Dependencies Missing**

**Error**: Various import errors for cv2, PIL, etc.

**Solution**:
```bash
# Install all requirements
cd packages/valthera
poetry install

# Install additional requirements
cd examples
poetry run pip install -r requirements.txt
```

## 🔧 Step-by-Step Setup

### **Option 1: Use Setup Script (Recommended)**

```bash
# Navigate to examples directory
cd packages/valthera/examples

# Make script executable and run
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### **Option 2: Manual Setup**

```bash
# 1. Navigate to valthera package
cd packages/valthera

# 2. Install dependencies
poetry install

# 3. Add PyTorch
poetry add torch torchvision

# 4. Navigate to examples
cd examples

# 5. Install additional requirements
poetry run pip install -r requirements.txt

# 6. Test basic functionality
poetry run python simple_test.py
```

## 🧪 Testing Sequence

### **1. Basic Environment Test**
```bash
poetry run python simple_test.py
```
This tests basic imports and PyTorch functionality.

### **2. Component Test**
```bash
poetry run python test_components.py
```
This tests the full valthera components.

### **3. Full Example Test**
```bash
# Quick test with minimal data
poetry run python droid_behavioral_cloning.py --num_videos 5 --epochs 2

# Full example
poetry run python droid_behavioral_cloning.py
```

## 🔍 Debug Information

### **Check Environment**
```bash
# Check Poetry environment
poetry env info

# Check installed packages
poetry show

# Check Python path
poetry run python -c "import sys; print('\n'.join(sys.path))"
```

### **Check File Structure**
```bash
# From valthera root
tree packages/valthera/examples -I "__pycache__"
tree packages/valthera/src/valthera/models/components -I "__pycache__"
```

### **Verbose Import Debugging**
```bash
# Run with verbose imports
PYTHONVERBOSE=1 poetry run python test_components.py
```

## 🐛 Common Debug Scenarios

### **Scenario 1: Fresh Installation**
```bash
# 1. Clean Poetry environment
cd packages/valthera
poetry env remove python

# 2. Reinstall
poetry install
poetry add torch torchvision

# 3. Test
cd examples
poetry run python simple_test.py
```

### **Scenario 2: Path Issues**
```bash
# 1. Check current directory
pwd

# 2. Verify file structure
ls -la
ls -la ../src/valthera/models/components/

# 3. Run with explicit path
PYTHONPATH="../src" poetry run python test_components.py
```

### **Scenario 3: Version Conflicts**
```bash
# 1. Check PyTorch version
poetry run python -c "import torch; print(torch.__version__)"

# 2. Update if needed
poetry add torch@latest torchvision@latest

# 3. Verify compatibility
poetry run python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## 📋 Environment Checklist

Before running the examples, ensure:

- [ ] Poetry is installed and in PATH
- [ ] You're in the correct directory (`packages/valthera/examples`)
- [ ] PyTorch is installed in Poetry environment
- [ ] All dependencies are installed
- [ ] File paths are correct
- [ ] Python version is compatible (3.8+)

## 🆘 Getting Help

If you're still having issues:

1. **Check the error message carefully**
2. **Verify your current directory**
3. **Run the simple test first**: `poetry run python simple_test.py`
4. **Check Poetry environment**: `poetry env info`
5. **Verify file structure**: `ls -la` and `ls -la ../src/valthera/`

## 📚 Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)
- [Python Path Issues](https://docs.python.org/3/tutorial/modules.html#the-module-search-path)
