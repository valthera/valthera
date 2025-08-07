#!/bin/bash
# Build script for video processor container
# This script builds the container with the correct environment variables

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building video processor container..."

# Check if required environment variables are provided
if [ -z "$SQS_QUEUE_URL" ]; then
    echo "Error: SQS_QUEUE_URL environment variable is required"
    exit 1
fi

if [ -z "$S3_BUCKET" ]; then
    echo "Error: S3_BUCKET environment variable is required"
    exit 1
fi

# Set default values
AWS_REGION="${AWS_REGION:-us-east-1}"
WORKER_LOG_LEVEL="${WORKER_LOG_LEVEL:-INFO}"

echo "Building with configuration:"
echo "  SQS_QUEUE_URL: $SQS_QUEUE_URL"
echo "  S3_BUCKET: $S3_BUCKET"
echo "  AWS_REGION: $AWS_REGION"
echo "  WORKER_LOG_LEVEL: $WORKER_LOG_LEVEL"

# Build the container using Docker
cd "$CONTAINER_DIR"

# Build the container with build arguments
docker build \
    --build-arg SQS_QUEUE_URL="$SQS_QUEUE_URL" \
    --build-arg S3_BUCKET="$S3_BUCKET" \
    --build-arg AWS_REGION="$AWS_REGION" \
    --build-arg WORKER_LOG_LEVEL="$WORKER_LOG_LEVEL" \
    -f Dockerfile.ec2 \
    -t video-processor:latest \
    .

echo "✅ Container built successfully"
echo "You can now run: docker run -d --name video-processor video-processor:latest" 