#!/bin/bash
set -e

# Log everything to both console and file
exec > >(tee /var/log/user-data.log) 2>&1

echo "=== Starting Video Processor Setup ==="

# Source environment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/env.sh" ]; then
    echo "Loading environment configuration from env.sh"
    source "${SCRIPT_DIR}/env.sh"
else
    echo "Warning: env.sh not found, using default environment variables"
    # Fallback to environment variables passed from user data
    SQS_QUEUE_URL="${SQS_QUEUE_URL}"
    S3_BUCKET="${S3_BUCKET}"
    AWS_REGION="${AWS_REGION:-us-east-1}"
fi

echo "Region: ${AWS_REGION}"
echo "SQS Queue: ${SQS_QUEUE_URL}"
echo "S3 Bucket: ${S3_BUCKET}"

# Update system packages (with retry logic)
echo "Updating system packages..."
for i in {1..3}; do
    if yum update -y; then
        echo "Package update successful on attempt $i"
        break
    else
        echo "Package update failed on attempt $i, retrying..."
        sleep 10
    fi
done

# Install Python 3.8 and development tools
echo "Installing Python and development tools..."
yum install -y python3 python3-pip python3-devel gcc gcc-c++ make

# Install Poetry
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"
echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc

# Install OpenCV dependencies
echo "Installing OpenCV dependencies..."
yum install -y opencv opencv-devel opencv-python

# Create application directory
echo "Setting up application directory..."
mkdir -p /opt/video-processor
cd /opt/video-processor

# Create environment file
echo "Creating environment configuration..."
cat > .env << EOF
SQS_QUEUE_URL=${SQS_QUEUE_URL}
S3_BUCKET=${S3_BUCKET}
AWS_REGION=${AWS_REGION}
AWS_DEFAULT_REGION=${AWS_REGION}
PYTHONUNBUFFERED=1
EOF

# Copy the video processor code
echo "Setting up video processor code..."
mkdir -p video_processor

# Create the worker.py file
cat > video_processor/worker.py << 'WORKER_EOF'
import os
import json
import boto3
import time
import logging
from pathlib import Path
import botocore.exceptions

import cv2
import numpy as np

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === Environment Variables ===
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
S3_BUCKET = os.environ["S3_BUCKET"]
REGION = os.environ.get("AWS_REGION", "us-east-1")

# === AWS Clients ===
sqs = boto3.client("sqs", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

logger.info(
    f"Initialized video processor with SQS: {SQS_QUEUE_URL}, "
    f"S3: {S3_BUCKET}"
)

# === Your embedding logic placeholder ===
def generate_embedding(video_path):
    """Generate embeddings from video frames"""
    logger.info(f"Generating embeddings for {video_path}")
    cap = cv2.VideoCapture(str(video_path))
    embeddings = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        mean = np.mean(frame, axis=(0, 1)).tolist()  # Mean RGB
        embeddings.append(mean)
        frame_count += 1
        
        # Log progress every 100 frames
        if frame_count % 100 == 0:
            logger.info(f"Processed {frame_count} frames")
    
    cap.release()
    logger.info(f"Generated embeddings for {frame_count} frames")
    return embeddings

# === Process a single job ===
def process_message(msg):
    """Process a single SQS message containing video processing job"""
    start_time = time.time()
    video_id = None
    
    try:        
        body = json.loads(msg["Body"])
        s3_key = body["s3_key"]  # e.g., "user123/videos/video.mp4"
        video_id = body.get("video_id", "unknown")
        
        logger.info(f"Processing job with S3 key: {s3_key}")

        # Check if the file exists
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=s3_key)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(
                    f"File not found: s3://{S3_BUCKET}/{s3_key}"
                )
                # Send metric for missing file
                cloudwatch.put_metric_data(
                    Namespace="VideoProcessor",
                    MetricData=[
                        {
                            "MetricName": "VideoProcessingErrors",
                            "Value": 1,
                            "Unit": "Count",
                            "Dimensions": [
                                {"Name": "ErrorType", "Value": "FileNotFound"},
                                {"Name": "VideoId", "Value": video_id}
                            ]
                        }
                    ]
                )
                return
            else:
                raise

        # Process the single video file
        if not s3_key.endswith(".mp4"):
            logger.warning(f"Skipping non-MP4 file: {s3_key}")
            # Send metric for unsupported file type
            cloudwatch.put_metric_data(
                Namespace="VideoProcessor",
                MetricData=[
                    {
                        "MetricName": "VideoProcessingErrors",
                        "Value": 1,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "ErrorType", "Value": "UnsupportedFileType"},
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    }
                ]
            )
            return

        logger.info(f"Processing: s3://{S3_BUCKET}/{s3_key}")
        local_path = Path("/tmp") / Path(s3_key).name
        
        try:
            # Download video file
            download_start = time.time()
            s3.download_file(S3_BUCKET, s3_key, str(local_path))
            download_time = time.time() - download_start
            logger.info(f"Downloaded {s3_key} to {local_path} in {download_time:.2f}s")

            # Run embedding
            processing_start = time.time()
            embedding = generate_embedding(local_path)
            processing_time = time.time() - processing_start

            # Save embedding locally
            embedding_path = str(local_path).replace(".mp4", ".embedding.json")
            with open(embedding_path, "w") as f:
                json.dump(embedding, f)

            # Upload embedding back to same folder
            upload_start = time.time()
            output_key = s3_key.replace(".mp4", ".embedding.json")
            s3.upload_file(embedding_path, S3_BUCKET, output_key)
            upload_time = time.time() - upload_start

            total_time = time.time() - start_time
            
            logger.info(
                f"✅ Successfully processed: s3://{S3_BUCKET}/{output_key}"
            )
            
            # Send success metrics
            cloudwatch.put_metric_data(
                Namespace="VideoProcessor",
                MetricData=[
                    {
                        "MetricName": "VideosProcessed",
                        "Value": 1,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    },
                    {
                        "MetricName": "ProcessingTime",
                        "Value": total_time,
                        "Unit": "Seconds",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    },
                    {
                        "MetricName": "DownloadTime",
                        "Value": download_time,
                        "Unit": "Seconds",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    },
                    {
                        "MetricName": "ProcessingTime",
                        "Value": processing_time,
                        "Unit": "Seconds",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    },
                    {
                        "MetricName": "UploadTime",
                        "Value": upload_time,
                        "Unit": "Seconds",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    },
                    {
                        "MetricName": "EmbeddingFrames",
                        "Value": len(embedding),
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    }
                ]
            )
            
            # Clean up local files
            local_path.unlink(missing_ok=True)
            Path(embedding_path).unlink(missing_ok=True)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing {s3_key}: {str(e)}")
            
            # Send error metrics
            cloudwatch.put_metric_data(
                Namespace="VideoProcessor",
                MetricData=[
                    {
                        "MetricName": "VideoProcessingErrors",
                        "Value": 1,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "ErrorType", "Value": "ProcessingError"},
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    },
                    {
                        "MetricName": "ProcessingTime",
                        "Value": processing_time,
                        "Unit": "Seconds",
                        "Dimensions": [
                            {"Name": "VideoId", "Value": video_id},
                            {"Name": "Status", "Value": "Failed"}
                        ]
                    }
                ]
            )
            raise
                
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing message: {str(e)}")
        
        # Send general error metric
        cloudwatch.put_metric_data(
            Namespace="VideoProcessor",
            MetricData=[
                {
                    "MetricName": "VideoProcessingErrors",
                    "Value": 1,
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "ErrorType", "Value": "GeneralError"},
                        {"Name": "VideoId", "Value": video_id or "unknown"}
                    ]
                }
            ]
        )
        raise

# === Main loop ===
def run_worker():
    """Main worker loop that continuously polls SQS for messages"""
    logger.info("Starting video processor worker...")
    
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            messages = response.get("Messages", [])
            if not messages:
                logger.debug("No messages received, continuing...")
                continue

            for msg in messages:
                try:
                    logger.info(f"Processing message: {msg['MessageId']}")
                    process_message(msg)

                    # Delete from SQS
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"]
                    )
                    logger.info("✅ SQS message deleted")

                except Exception as e:
                    logger.error(
                        f"Error processing message "
                        f"{msg.get('MessageId', 'unknown')}: {str(e)}"
                    )
                    # Don't delete the message so it can be retried
                    continue

        except botocore.exceptions.ClientError as e:
            logger.error(f"AWS error: {e}")
            time.sleep(5)  # Wait longer on AWS errors
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_worker()
WORKER_EOF

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "video-processor"
version = "0.1.0"
description = "Video processing worker for SQS"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.8"
boto3 = "^1.26.0"
opencv-python = "^4.8.0"
numpy = "^1.24.0"
python-dotenv = "^1.0.0"

[tool.poetry.dev-dependencies]

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
EOF

# Install dependencies with Poetry
echo "Installing dependencies with Poetry..."
export PATH="/root/.local/bin:$PATH"
poetry install --no-dev

# Create systemd service for the worker
echo "Creating systemd service..."
cat > /etc/systemd/system/video-processor.service << 'EOF'
[Unit]
Description=Video Processor Worker
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/video-processor
Environment=PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/.local/bin/poetry run python video_processor/worker.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "Enabling and starting video processor service..."
systemctl daemon-reload
systemctl enable video-processor.service
systemctl start video-processor.service

# Wait a moment and check status
sleep 5
if systemctl is-active --quiet video-processor.service; then
    echo "✅ Video processor service started successfully"
    systemctl status video-processor.service
else
    echo "❌ Video processor service failed to start"
    systemctl status video-processor.service
    journalctl -u video-processor.service -n 20
    exit 1
fi

echo "=== Video Processor Setup Complete ==="
