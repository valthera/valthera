#!/bin/bash

# DROID Behavioral Cloning Example - Setup and Run Script

echo "🚀 Setting up DROID Behavioral Cloning Example"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "droid_behavioral_cloning.py" ]; then
    echo "❌ Error: Please run this script from the examples directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: droid_behavioral_cloning.py, test_components.py"
    exit 1
fi

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed or not in PATH"
    echo "   Please install Poetry first: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Navigate to the valthera package directory
cd ..

echo "📦 Installing dependencies..."
poetry install

# Check if PyTorch is available
echo "🔍 Checking PyTorch installation..."
if ! poetry run python -c "import torch; print(f'PyTorch version: {torch.__version__}')" 2>/dev/null; then
    echo "📥 Installing PyTorch..."
    poetry add torch torchvision
fi

# Install additional requirements
echo "📥 Installing additional requirements..."
cd examples
poetry run pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🧪 To test components:"
echo "   poetry run python test_components.py"
echo ""
echo "🚀 To run full example:"
echo "   poetry run python droid_behavioral_cloning.py"
echo ""
echo "🔧 To run with custom parameters:"
echo "   poetry run python droid_behavioral_cloning.py --num_videos 100 --epochs 30"
echo ""
echo "📚 For more options, see: python droid_behavioral_cloning.py --help"
