#!/bin/bash

# Multi-architecture build script for Camera Docker container
# Builds for both x86_64 (Mac development) and ARM64 (Jetson Nano)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Multi-architecture Camera Docker Build${NC}"
echo "=========================================="

# Check if buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker buildx not available${NC}"
    echo "Please install Docker buildx or enable experimental features"
    exit 1
fi

# Create and use a new builder instance for multi-arch builds
echo -e "${YELLOW}📦 Setting up multi-architecture builder...${NC}"
docker buildx create --name multiarch-builder --use --driver docker-container 2>/dev/null || true

# Build for multiple architectures
echo -e "${YELLOW}🔨 Building multi-architecture image...${NC}"
echo "Target platforms: linux/amd64 (Mac), linux/arm64 (Jetson Nano)"

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag camera:latest \
    --tag camera:multiarch \
    --push \
    .

echo -e "${GREEN}✅ Multi-architecture build completed!${NC}"
echo ""
echo -e "${BLUE}📋 Usage Instructions:${NC}"
echo "  • For Mac development: docker run --rm camera:latest"
echo "  • For Jetson Nano: docker run --rm --runtime nvidia --gpus all camera:latest"
echo ""
echo -e "${BLUE}🔍 To test on Jetson Nano:${NC}"
echo "  docker run --rm --runtime nvidia --gpus all \\"
echo "    --privileged -v /dev/bus/usb:/dev/bus/usb \\"
echo "    camera:latest" 