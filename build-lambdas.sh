#!/bin/bash
# Build Lambda Functions
# This script builds all Lambda functions with their dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create build directory
BUILD_DIR="lambdas-built"
log_info "Creating build directory: $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Function to build a domain's Lambda functions
build_domain() {
    local domain_dir=$1
    local domain_name=$(basename "$domain_dir")
    
    log_info "Building domain: $domain_name"
    
    # Create build directory for this domain
    local build_path="$BUILD_DIR/$domain_name"
    mkdir -p "$build_path"
    
    # Copy all Lambda function directories preserving structure
    for lambda_dir in "$domain_dir"/*/; do
        if [[ -d "$lambda_dir" ]]; then
            local lambda_name=$(basename "$lambda_dir")
            log_info "  Copying $lambda_name"
            cp -r "$lambda_dir" "$build_path/" 2>/dev/null || true
        fi
    done
    
    # Install dependencies if pyproject.toml exists
    if [[ -f "$domain_dir/pyproject.toml" ]]; then
        log_info "Installing Poetry dependencies for $domain_name"
        cd "$domain_dir"
        poetry install --only main
        cd "$SCRIPT_DIR"
        # Copy installed packages from .venv to build directory
        if [[ -d "$domain_dir/.venv/lib" ]]; then
            python_lib_dir=$(find "$domain_dir/.venv/lib" -name "python*" -type d | head -1)
            if [[ -n "$python_lib_dir" ]]; then
                log_info "Copying dependencies from $python_lib_dir/site-packages"
                cp -r "$python_lib_dir/site-packages/"* "$build_path/" 2>/dev/null || true
            fi
        fi
    fi
    
    # Copy valthera-core package to build directory (after Poetry install to ensure latest version)
    if [[ -d "packages/valthera-core" ]]; then
        log_info "  Copying valthera-core package"
        cp -r "packages/valthera-core/valthera_core" "$build_path/" 2>/dev/null || true
    fi
    
    # Create deployment package
    cd "$build_path"
    zip -r "../${domain_name}.zip" . -x "*.pyc" "__pycache__/*" "*.pyo" "*.pyd" ".Python" "env/*" "venv/*" ".venv/*"
    cd "$SCRIPT_DIR"
    
    log_success "Built domain $domain_name"
}

# Build all Lambda functions
log_info "Building all Lambda functions..."

# Build account Lambda functions
if [[ -d "lambdas/account" ]]; then
    build_domain "lambdas/account"
fi

# Build meter Lambda functions
if [[ -d "lambdas/meter" ]]; then
    build_domain "lambdas/meter"
fi

# Build data Lambda functions
if [[ -d "lambdas/data" ]]; then
    build_domain "lambdas/data"
fi

# Build projects Lambda functions
if [[ -d "lambdas/projects" ]]; then
    build_domain "lambdas/projects"
fi

# Build behaviors Lambda functions
if [[ -d "lambdas/behaviors" ]]; then
    build_domain "lambdas/behaviors"
fi

# Build datasources Lambda functions
if [[ -d "lambdas/datasources" ]]; then
    build_domain "lambdas/datasources"
fi

# Build training Lambda functions
if [[ -d "lambdas/training" ]]; then
    build_domain "lambdas/training"
fi

# Build endpoints Lambda functions
if [[ -d "lambdas/endpoints" ]]; then
    build_domain "lambdas/endpoints"
fi

# Create build info
echo "Build completed at $(date)" > "$BUILD_DIR/build_info.txt"
echo "Build script: $0" >> "$BUILD_DIR/build_info.txt"
echo "Build directory: $BUILD_DIR" >> "$BUILD_DIR/build_info.txt"

log_success "All Lambda functions built successfully!"
log_info "Build artifacts in: $BUILD_DIR" 