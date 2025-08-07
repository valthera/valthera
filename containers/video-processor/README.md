# Video Processor Container

This container provides video processing capabilities for the Valthera infrastructure.

## Architecture

The video processor is designed to run on EC2 instances and process video files from SQS queues. It uses a configurable build process that allows environment variables to be set during the container build phase.

## Files Structure

```
containers/video-processor/
├── Dockerfile              # Standard container for local development
├── Dockerfile.ec2          # EC2-specific container with systemd
├── scripts/
│   ├── setup.sh            # Main setup script for EC2 instances
│   ├── env.sh              # Environment configuration template
│   ├── build-env.sh        # Script to populate env.sh during build
│   └── build-container.sh  # Container build script with environment variables
├── video_processor/
│   ├── __init__.py
│   ├── worker.py           # Main worker implementation
│   └── worker_simple.py    # Simplified worker for local testing
├── pyproject.toml          # Poetry dependencies
└── README.md
```

## Configuration

The container uses environment variables for configuration:

- `SQS_QUEUE_URL`: URL of the SQS queue to poll for video processing jobs
- `S3_BUCKET`: S3 bucket name for video storage
- `AWS_REGION`: AWS region (defaults to us-east-1)
- `WORKER_LOG_LEVEL`: Logging level (defaults to INFO)

## Build Process

### Option 1: Using build-container.sh (Recommended)

```bash
# Set environment variables
export SQS_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/123456789012/dev-video-queue"
export S3_BUCKET="dev-video-bucket"
export AWS_REGION="us-east-1"

# Build the container
./scripts/build-container.sh
```

### Option 2: Direct Docker build

```bash
docker build \
    --build-arg SQS_QUEUE_URL="$SQS_QUEUE_URL" \
    --build-arg S3_BUCKET="$S3_BUCKET" \
    --build-arg AWS_REGION="$AWS_REGION" \
    -f Dockerfile.ec2 \
    -t video-processor:latest \
    .
```

## Deployment

### Local Development

```bash
# Build and run locally
docker build -f Dockerfile -t video-processor:dev .
docker run -e SQS_QUEUE_URL="$SQS_QUEUE_URL" \
           -e S3_BUCKET="$S3_BUCKET" \
           -e AWS_REGION="$AWS_REGION" \
           video-processor:dev
```

### EC2 Deployment

The container is designed to work with the CDK infrastructure. The CDK stack will:

1. Set environment variables during the build process
2. Create the `env.sh` file with the correct configuration
3. Deploy the container to EC2 instances
4. Start the video processor service

## How It Works

1. **Build Phase**: The `build-env.sh` script creates an `env.sh` file with the environment variables
2. **Setup Phase**: The `setup.sh` script sources the `env.sh` file and sets up the EC2 instance
3. **Runtime**: The worker polls the SQS queue for video processing jobs
4. **Processing**: Videos are downloaded from S3, processed to generate embeddings, and results are uploaded back to S3

## Environment Configuration

The `env.sh` file is created during the build process and contains:

```bash
#!/bin/bash
# Environment configuration for video processor

# AWS Configuration
export SQS_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/123456789012/dev-video-queue"
export S3_BUCKET="dev-video-bucket"
export AWS_REGION="us-east-1"

# Application Configuration
export PYTHONUNBUFFERED=1
export WORKER_LOG_LEVEL="INFO"
```

## Benefits of This Approach

1. **Configurable**: Environment variables are set during build time, not runtime
2. **No String Embedding**: No need to embed large strings in CDK code
3. **Maintainable**: Easy to modify configuration without changing infrastructure code
4. **Testable**: Can be built and tested locally with different configurations
5. **Standard**: Follows container best practices for configuration management

## Troubleshooting

### Container Build Issues

- Ensure all required environment variables are set
- Check that Docker is running
- Verify the Dockerfile.ec2 exists and is correct

### Runtime Issues

- Check the systemd service status: `systemctl status video-processor.service`
- View logs: `journalctl -u video-processor.service -f`
- Verify environment variables: `source /opt/video-processor/scripts/env.sh && env | grep -E "(SQS|S3|AWS)"`

### SQS/S3 Issues

- Verify IAM permissions for the EC2 instance
- Check that the SQS queue and S3 bucket exist
- Ensure the AWS region is correct
