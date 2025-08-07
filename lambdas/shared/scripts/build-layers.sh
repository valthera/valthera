#!/bin/bash

# Build script for Lambda layers
# This script builds all layers using Poetry

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAYERS_DIR="$(dirname "$SCRIPT_DIR")/../layers"

echo "Building Lambda layers..."

# Function to build a layer
build_layer() {
    local layer_name=$1
    local layer_dir="$LAYERS_DIR/$layer_name"
    
    echo "Building layer: $layer_name"
    
    if [ ! -d "$layer_dir" ]; then
        echo "Error: Layer directory $layer_dir does not exist"
        return 1
    fi
    
    cd "$layer_dir"
    
    # Check if pyproject.toml exists
    if [ ! -f "pyproject.toml" ]; then
        echo "Error: pyproject.toml not found in $layer_dir"
        return 1
    fi
    
    # Install dependencies using Poetry
    echo "Installing dependencies for $layer_name..."
    poetry install --no-dev --no-root
    
    # Create python directory if it doesn't exist
    mkdir -p python
    
    # Copy dependencies to python directory
    echo "Copying dependencies to python directory..."
    poetry export -f requirements.txt --output requirements.txt --without-hashes
    pip install -r requirements.txt -t python/
    
    # Clean up
    rm requirements.txt
    
    echo "Layer $layer_name built successfully"
}

# Build all layers
for layer_dir in "$LAYERS_DIR"/*/; do
    if [ -d "$layer_dir" ]; then
        layer_name=$(basename "$layer_dir")
        build_layer "$layer_name"
    fi
done

echo "All layers built successfully!" 