#!/bin/bash
# Build script to populate environment configuration
# This script is called during the container build process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/env.sh"

echo "Building environment configuration..."

# Check if required environment variables are provided
if [ -z "$SQS_QUEUE_URL" ]; then
    echo "Error: SQS_QUEUE_URL environment variable is required"
    exit 1
fi

if [ -z "$S3_BUCKET" ]; then
    echo "Error: S3_BUCKET environment variable is required"
    exit 1
fi

# Create the env.sh file with the provided values
cat > "$ENV_FILE" << EOF
#!/bin/bash
# Environment configuration for video processor
# This file is populated during the container build process

# AWS Configuration
export SQS_QUEUE_URL="$SQS_QUEUE_URL"
export S3_BUCKET="$S3_BUCKET"
export AWS_REGION="${AWS_REGION:-us-east-1}"

# Application Configuration
export PYTHONUNBUFFERED=1
export WORKER_LOG_LEVEL="${WORKER_LOG_LEVEL:-INFO}"
EOF

echo "Environment configuration written to $ENV_FILE"
echo "SQS_QUEUE_URL: $SQS_QUEUE_URL"
echo "S3_BUCKET: $S3_BUCKET"
echo "AWS_REGION: ${AWS_REGION:-us-east-1}" 