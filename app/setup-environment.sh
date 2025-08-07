#!/bin/bash

# Setup Environment for Frontend Build
# This script helps set up the required environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up environment for frontend build...${NC}"
echo ""

# Check if we're in the app directory
if [[ ! -f "package.json" ]]; then
    echo -e "${RED}❌ Please run this script from the app directory${NC}"
    exit 1
fi

# Check if .env.production exists
if [[ ! -f ".env.production" ]]; then
    echo -e "${YELLOW}⚠️  .env.production not found, creating from template...${NC}"
    cp env.production.template .env.production
    echo -e "${GREEN}✅ Created .env.production from template${NC}"
fi

# Check if CDK outputs exist
if [[ -f "cdk-outputs.json" ]]; then
    echo -e "${BLUE}📋 Found CDK outputs, checking for environment variables...${NC}"
    
    # Extract values from CDK outputs if they exist
    if command -v jq >/dev/null 2>&1; then
        # Try to extract values from CDK outputs
        API_BASE_URL=$(jq -r '.outputs.ApiGatewayUrl // empty' cdk-outputs.json 2>/dev/null)
        USER_POOL_ID=$(jq -r '.outputs.UserPoolId // empty' cdk-outputs.json 2>/dev/null)
        USER_POOL_CLIENT_ID=$(jq -r '.outputs.UserPoolClientId // empty' cdk-outputs.json 2>/dev/null)
        IDENTITY_POOL_ID=$(jq -r '.outputs.IdentityPoolId // empty' cdk-outputs.json 2>/dev/null)
        API_KEY=$(jq -r '.outputs.ApiKey // empty' cdk-outputs.json 2>/dev/null)
        
        if [[ -n "$API_BASE_URL" ]]; then
            echo -e "${GREEN}✅ Found API_BASE_URL: $API_BASE_URL${NC}"
        fi
        if [[ -n "$USER_POOL_ID" ]]; then
            echo -e "${GREEN}✅ Found USER_POOL_ID: $USER_POOL_ID${NC}"
        fi
        if [[ -n "$USER_POOL_CLIENT_ID" ]]; then
            echo -e "${GREEN}✅ Found USER_POOL_CLIENT_ID: $USER_POOL_CLIENT_ID${NC}"
        fi
        if [[ -n "$IDENTITY_POOL_ID" ]]; then
            echo -e "${GREEN}✅ Found IDENTITY_POOL_ID: $IDENTITY_POOL_ID${NC}"
        fi
        if [[ -n "$API_KEY" ]]; then
            echo -e "${GREEN}✅ Found API_KEY: $API_KEY${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  jq not found, cannot parse CDK outputs${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No CDK outputs found${NC}"
fi

# Check if environment variables are set
echo ""
echo -e "${BLUE}🔍 Checking required environment variables...${NC}"

REQUIRED_VARS=(
    "VITE_API_BASE_URL"
    "VITE_COGNITO_USER_POOL_ID"
    "VITE_COGNITO_USER_POOL_CLIENT_ID"
    "VITE_COGNITO_IDENTITY_POOL_ID"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        MISSING_VARS+=("$var")
        echo -e "${RED}❌ Missing: $var${NC}"
    else
        echo -e "${GREEN}✅ Found: $var${NC}"
    fi
done

echo ""

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Some environment variables are missing${NC}"
    echo -e "${BLUE}💡 You have a few options:${NC}"
    echo ""
    echo -e "${BLUE}1. Deploy the CDK infrastructure first:${NC}"
    echo -e "   cd ../cdk && npm run deploy"
    echo ""
    echo -e "${BLUE}2. Use the switch-environment script:${NC}"
    echo -e "   ./scripts/switch-environment.sh dev valthera-dev"
    echo ""
    echo -e "${BLUE}3. Manually set the environment variables in .env.production${NC}"
    echo -e "   Edit .env.production with your actual values"
    echo ""
    echo -e "${BLUE}4. Use development mode (if you have local API running):${NC}"
    echo -e "   npm run dev"
    echo ""
    echo -e "${YELLOW}⚠️  The build will fail without these variables${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All required environment variables are set${NC}"
    echo ""
    echo -e "${BLUE}🚀 You can now build the frontend:${NC}"
    echo -e "   npm run build"
    echo ""
    echo -e "${BLUE}Or run in development mode:${NC}"
    echo -e "   npm run dev"
fi

echo ""
echo -e "${BLUE}📋 Environment files:${NC}"
ls -la .env* 2>/dev/null || echo "No .env files found"

echo ""
echo -e "${GREEN}✅ Environment setup complete!${NC}" 