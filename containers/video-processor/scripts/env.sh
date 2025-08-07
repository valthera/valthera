#!/bin/bash
# Environment configuration for video processor
# This file is populated during the container build process

# AWS Configuration
export SQS_QUEUE_URL="${SQS_QUEUE_URL:-}"
export S3_BUCKET="${S3_BUCKET:-}"
export AWS_REGION="${AWS_REGION:-us-east-1}"

# Application Configuration
export PYTHONUNBUFFERED=1
export WORKER_LOG_LEVEL="${WORKER_LOG_LEVEL:-INFO}"

# Optional: Override default values for development/testing
# export SQS_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/123456789012/dev-video-processor-queue"
# export S3_BUCKET="dev-video-bucket"
# export AWS_REGION="us-east-1" 