#!/bin/bash

# Build and publish Camera Docker container to Docker Hub
# Repository: vselvarajijay/valthera-camera

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REPO="vselvarajijay/valthera-camera"
IMAGE_NAME="valthera-camera"
VERSION=${1:-"latest"}
BUILD_MULTIARCH=${2:-"true"}

echo -e "${BLUE}🚀 Valthera Camera Docker Build & Publish${NC}"
echo "=============================================="
echo -e "${PURPLE}Repository:${NC} $DOCKER_REPO"
echo -e "${PURPLE}Version:${NC} $VERSION"
echo -e "${PURPLE}Multi-arch:${NC} $BUILD_MULTIARCH"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check if user is logged in to Docker Hub
if ! docker info | grep -q "Username:"; then
    echo -e "${YELLOW}⚠️  Not logged in to Docker Hub${NC}"
    echo "Please run: docker login"
    read -p "Press Enter to continue after logging in, or Ctrl+C to exit..."
fi

# Function to build single architecture
build_single() {
    local arch=$1
    local tag=$2
    
    echo -e "${YELLOW}🔨 Building for $arch...${NC}"
    docker build \
        --platform linux/$arch \
        --tag $tag \
        .
}

# Function to build and push multi-architecture
build_multiarch() {
    echo -e "${YELLOW}🔨 Building multi-architecture image...${NC}"
    echo "Target platforms: linux/amd64, linux/arm64"
    
    # Create and use a new builder instance for multi-arch builds
    echo -e "${YELLOW}📦 Setting up multi-architecture builder...${NC}"
    docker buildx create --name valthera-builder --use --driver docker-container 2>/dev/null || true
    
    # Build and push for multiple architectures
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag $DOCKER_REPO:$VERSION \
        --tag $DOCKER_REPO:latest \
        --push \
        .
}

# Function to build and push single architecture
build_and_push_single() {
    local arch=$1
    local tag=$DOCKER_REPO:$VERSION-$arch
    
    echo -e "${YELLOW}🔨 Building and pushing for $arch...${NC}"
    
    docker build \
        --platform linux/$arch \
        --tag $tag \
        --tag $DOCKER_REPO:latest-$arch \
        .
    
    docker push $tag
    docker push $DOCKER_REPO:latest-$arch
}

# Main build logic
if [ "$BUILD_MULTIARCH" = "true" ]; then
    # Check if buildx is available
    if ! docker buildx version > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker buildx not available${NC}"
        echo "Please install Docker buildx or enable experimental features"
        echo "Falling back to single architecture build..."
        BUILD_MULTIARCH="false"
    fi
fi

if [ "$BUILD_MULTIARCH" = "true" ]; then
    build_multiarch
    echo -e "${GREEN}✅ Multi-architecture build and push completed!${NC}"
else
    echo -e "${YELLOW}🔨 Building single architecture images...${NC}"
    
    # Build for both architectures separately
    build_and_push_single "amd64"
    build_and_push_single "arm64"
    
    echo -e "${GREEN}✅ Single architecture builds and pushes completed!${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Successfully published to Docker Hub!${NC}"
echo ""
echo -e "${BLUE}📋 Published Images:${NC}"
echo "  • $DOCKER_REPO:$VERSION"
echo "  • $DOCKER_REPO:latest"
if [ "$BUILD_MULTIARCH" = "false" ]; then
    echo "  • $DOCKER_REPO:$VERSION-amd64"
    echo "  • $DOCKER_REPO:$VERSION-arm64"
    echo "  • $DOCKER_REPO:latest-amd64"
    echo "  • $DOCKER_REPO:latest-arm64"
fi
echo ""
echo -e "${BLUE}🚀 Usage Examples:${NC}"
echo ""
echo -e "${PURPLE}For Mac/Linux (x86_64):${NC}"
echo "  docker run --rm -p 8000:8000 $DOCKER_REPO:latest"
echo ""
echo -e "${PURPLE}For Jetson Nano (ARM64):${NC}"
echo "  docker run --rm --runtime nvidia --gpus all \\"
echo "    --privileged -v /dev/bus/usb:/dev/bus/usb \\"
echo "    -p 8000:8000 $DOCKER_REPO:latest"
echo ""
echo -e "${PURPLE}With specific version:${NC}"
echo "  docker run --rm -p 8000:8000 $DOCKER_REPO:$VERSION"
echo ""
echo -e "${BLUE}🔍 Test the container:${NC}"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/viewer"
echo ""
echo -e "${GREEN}✨ Build and publish completed successfully!${NC}"
