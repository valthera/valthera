#!/bin/bash
# Switch to a different environment for local development
# Usage: ./scripts/switch-environment.sh [environment] [profile]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_ENVIRONMENT="dev"
DEFAULT_PROFILE="valthera-dev"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
CDK_DIR="$(dirname "$APP_DIR")/cdk"

# Parse arguments

# Auto-determine environment from profile if not specified
determine_environment_from_profile

# Load profile-to-environment mapping
load_profile_mapping() {
    local mapping_file="$(dirname "$SCRIPT_DIR")/cdk/config/profile-environments.conf"
    
    if [[ -f "$mapping_file" ]]; then
        # Source the mapping file
        set -a
        source "$mapping_file"
        set +a
        return 0
    else
        echo -e "${YELLOW}⚠️  Profile mapping file not found: $mapping_file${NC}"
        return 1
    fi
}

# Auto-determine environment from profile
determine_environment_from_profile() {
    if [[ -z "$ENVIRONMENT" && -n "$PROFILE" ]]; then
        # Try to load profile mapping
        if load_profile_mapping; then
            # Check if profile has a direct mapping
            local mapped_env="${!PROFILE}"
            if [[ -n "$mapped_env" ]]; then
                ENVIRONMENT="$mapped_env"
                echo -e "${BLUE}🔄 Mapped environment: $ENVIRONMENT from profile: $PROFILE${NC}"
                return 0
            fi
        fi
        
        # Fallback to pattern matching
        if [[ "$PROFILE" == *"-dev" ]]; then
            ENVIRONMENT="dev"
        elif [[ "$PROFILE" == *"-staging" ]]; then
            ENVIRONMENT="staging"
        elif [[ "$PROFILE" == *"-prod" ]]; then
            ENVIRONMENT="prod"
        else
            ENVIRONMENT="dev"
        fi
        echo -e "${BLUE}📋 Auto-detected environment: $ENVIRONMENT from profile: $PROFILE${NC}"
    fi
}
ENVIRONMENT=${1:-$DEFAULT_ENVIRONMENT}
PROFILE=${2:-valthera-${ENVIRONMENT}}

echo -e "${BLUE}🔄 Switching to environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}   Using AWS profile: ${PROFILE}${NC}"
echo ""

# Validate environment
valid_environments=("dev" "staging" "prod")
if [[ ! " ${valid_environments[@]} " =~ " ${ENVIRONMENT} " ]]; then
    echo -e "${RED}❌ Invalid environment: ${ENVIRONMENT}${NC}"
    echo -e "${YELLOW}   Valid environments: ${valid_environments[*]}${NC}"
    exit 1
fi

# Check if AWS profile exists
if ! aws configure list-profiles | grep -q "$PROFILE"; then
    echo -e "${RED}❌ AWS profile not found: ${PROFILE}${NC}"
    echo -e "${YELLOW}   Please configure the profile first:${NC}"
    echo -e "${YELLOW}   aws configure --profile ${PROFILE}${NC}"
    exit 1
fi

# Test AWS access
echo -e "${BLUE}🔍 Testing AWS access...${NC}"
if ! aws sts get-caller-identity --profile "$PROFILE" >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot access AWS with profile ${PROFILE}${NC}"
    echo -e "${YELLOW}   Please check your AWS credentials${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS access verified${NC}"
echo ""

# Extract CDK outputs for this environment
echo -e "${BLUE}📦 Extracting CDK outputs...${NC}"
cd "$CDK_DIR"

if [[ ! -f "scripts/utils/extract-outputs.py" ]]; then
    echo -e "${RED}❌ CDK output extraction script not found${NC}"
    exit 1
fi

if ! python3 scripts/utils/extract-outputs.py \
    --profile "$PROFILE" \
    --environment "$ENVIRONMENT" \
    --output-dir "../app"; then
    echo -e "${RED}❌ Failed to extract CDK outputs${NC}"
    echo -e "${YELLOW}   Make sure the CDK stacks are deployed for this environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ CDK outputs extracted successfully${NC}"
echo ""

# Update app configuration
cd "$APP_DIR"
echo -e "${BLUE}📝 Updating app configuration...${NC}"

# Create environment-specific .env.local file
cat > .env.local << EOF
# Environment configuration for ${ENVIRONMENT}
# Generated on: $(date)
VITE_ENVIRONMENT=${ENVIRONMENT}
VITE_AWS_PROFILE=${PROFILE}
EOF

echo -e "${GREEN}✅ App configuration updated${NC}"
echo ""

# Display environment information
echo -e "${BLUE}📋 Environment Information:${NC}"
echo -e "   Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "   AWS Profile: ${GREEN}${PROFILE}${NC}"
echo -e "   Configuration files:"
echo -e "     - ${GREEN}.env.local${NC} (highest precedence)"
echo -e "     - ${GREEN}.env.production${NC}"
echo -e "     - ${GREEN}.env${NC}"
echo -e "     - ${GREEN}environments/${ENVIRONMENT}/.env${NC}"

# Check if environment files exist
env_files=(".env.local" ".env.production" ".env" "environments/${ENVIRONMENT}/.env")
for file in "${env_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "     ✅ ${file}"
    else
        echo -e "     ❌ ${file} (missing)"
    fi
done

echo ""
echo -e "${GREEN}✅ Successfully switched to environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}   You can now run your local app with:${NC}"
echo -e "${YELLOW}   npm run dev${NC}"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo -e "   - The app will use the ${ENVIRONMENT} environment configuration"
echo -e "   - CDK outputs are stored in environments/${ENVIRONMENT}/"
echo -e "   - To switch environments again, run this script with different arguments"
echo -e "   - Example: ./scripts/switch-environment.sh staging valthera-staging" 