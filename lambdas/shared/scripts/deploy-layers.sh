#!/bin/bash

# Deploy script for Lambda layers
# This script builds and deploys layers to AWS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAYERS_DIR="$(dirname "$SCRIPT_DIR")/../layers"

# Default values
ENVIRONMENT=${ENVIRONMENT:-dev}
REGION=${AWS_REGION:-us-east-1}
STACK_NAME="valthera-layers-${ENVIRONMENT}"

echo "Deploying Lambda layers..."
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack Name: $STACK_NAME"

# Function to deploy a layer
deploy_layer() {
    local layer_name=$1
    local layer_dir="$LAYERS_DIR/$layer_name"
    
    echo "Deploying layer: $layer_name"
    
    if [ ! -d "$layer_dir" ]; then
        echo "Error: Layer directory $layer_dir does not exist"
        return 1
    fi
    
    cd "$layer_dir"
    
    # Build the layer (no Poetry; use requirements.txt if present)
    echo "Building layer $layer_name..."
    mkdir -p python
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -t python/
    fi
    
    # Create zip file
    echo "Creating zip file for $layer_name..."
    zip -r "${layer_name}.zip" python/ ffmpeg ffprobe 2>/dev/null || zip -r "${layer_name}.zip" python/
    
    # Deploy to AWS
    echo "Deploying $layer_name to AWS..."
    aws lambda publish-layer-version \
        --layer-name "valthera-${layer_name}-${ENVIRONMENT}" \
        --description "Valthera ${layer_name} layer for ${ENVIRONMENT} environment" \
        --zip-file "fileb://${layer_name}.zip" \
        --compatible-runtimes python3.9 \
        --compatible-architectures x86_64 \
        --region "$REGION"
    
    # Clean up
    rm "${layer_name}.zip"
    rm -rf python/
    
    echo "Layer $layer_name deployed successfully"
}

# Deploy all layers
for layer_dir in "$LAYERS_DIR"/*/; do
    if [ -d "$layer_dir" ]; then
        layer_name=$(basename "$layer_dir")
        deploy_layer "$layer_name"
    fi
done

echo "All layers deployed successfully!"

# Output layer ARNs for reference
echo ""
echo "Layer ARNs:"
aws lambda list-layers --region "$REGION" --query "Layers[?contains(LayerName, 'valthera')].{Name: LayerName, LatestVersion: LatestMatchingVersion.LayerVersionArn}" --output table 