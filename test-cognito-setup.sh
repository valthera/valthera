#!/bin/bash

# Test script to verify Cognito setup
set -e

echo "🧪 Testing Cognito Setup"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ [SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  [WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}❌ [ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️  [INFO]${NC} $1"
}

# Check if Cognito container is running
print_info "Checking if Cognito container is running..."
if docker ps --filter "name=valthera-cognito-local" --format "table {{.Status}}" | grep -q "Up"; then
    print_success "Cognito container is running"
else
    print_error "Cognito container is not running"
    print_info "Start it with: ./valthera-local start"
    exit 1
fi

# Check if Cognito service is responding
print_info "Checking if Cognito service is responding..."
if curl -s http://localhost:9239 >/dev/null 2>&1; then
    print_success "Cognito service is responding"
else
    print_error "Cognito service is not responding"
    print_info "Check logs with: docker logs valthera-cognito-local"
    exit 1
fi

# Check if .env.local file exists
print_info "Checking if .env.local file exists..."
if [ -f "app/.env.local" ]; then
    print_success "app/.env.local file exists"
    
    # Check if it has Cognito configuration
    if grep -q "VITE_COGNITO_USER_POOL_ID" app/.env.local; then
        print_success "Cognito configuration found in .env.local"
        
        # Extract and display the configuration
        USER_POOL_ID=$(grep VITE_COGNITO_USER_POOL_ID app/.env.local | cut -d'=' -f2)
        CLIENT_ID=$(grep VITE_COGNITO_USER_POOL_CLIENT_ID app/.env.local | cut -d'=' -f2)
        
        echo "  User Pool ID: $USER_POOL_ID"
        echo "  Client ID: $CLIENT_ID"
    else
        print_warning "Cognito configuration not found in .env.local"
    fi
else
    print_warning "app/.env.local file not found"
    print_info "Run: ./valthera-local setup-cognito"
fi

# Test AWS CLI connectivity to Cognito
print_info "Testing AWS CLI connectivity to Cognito..."
if aws cognito-idp list-user-pools --max-results 10 --endpoint-url http://localhost:9239 --region us-east-1 >/dev/null 2>&1; then
    print_success "AWS CLI can connect to Cognito"
else
    print_error "AWS CLI cannot connect to Cognito"
    print_info "Check if AWS CLI is installed and configured"
    exit 1
fi

# Test if user pool exists
print_info "Checking if user pool exists..."
if aws cognito-idp list-user-pools --max-results 10 --endpoint-url http://localhost:9239 --region us-east-1 | grep -q "valthera-local-pool"; then
    print_success "User pool 'valthera-local-pool' exists"
else
    print_warning "User pool 'valthera-local-pool' not found"
    print_info "Run: ./valthera-local setup-cognito"
fi

echo ""
print_success "🎉 Cognito setup test completed!"
print_info "If you see any warnings above, run: ./valthera-local setup-cognito" 