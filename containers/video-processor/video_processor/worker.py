import os
import json
import boto3
import time
import logging
from pathlib import Path
import botocore.exceptions
from botocore.config import Config

import cv2
import numpy as np

from dotenv import load_dotenv
load_dotenv()

# Add valthera-core to path if available
try:
    from valthera_core import get_sqs_client
    USE_VALTHERA_CORE = True
except ImportError:
    USE_VALTHERA_CORE = False
    print("Warning: valthera_core not available, using direct boto3 client")

# Configure logging
log_level = os.environ.get("WORKER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('/app/logs/worker.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

# === Environment Variables ===
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
S3_BUCKET = os.environ["S3_BUCKET"]
REGION = os.environ.get("AWS_REGION", "us-east-1")

# === AWS Clients ===
# Configure retry settings for better resilience
boto_config = Config(
    region_name=REGION,
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    }
)

# Use centralized SQS client if available, otherwise fallback to direct boto3
if USE_VALTHERA_CORE:
    sqs = get_sqs_client()
else:
    sqs_kwargs = {'config': boto_config}
    if os.environ.get('SQS_ENDPOINT_URL'):
        sqs_kwargs['endpoint_url'] = os.environ.get('SQS_ENDPOINT_URL')
    sqs = boto3.client("sqs", **sqs_kwargs)

s3 = boto3.client("s3", config=boto_config)
cloudwatch = boto3.client("cloudwatch", config=boto_config)

logger.info(
    f"Initialized video processor with SQS: {SQS_QUEUE_URL}, "
    f"S3: {S3_BUCKET}"
)


# === AWS Credential Validation ===
def validate_aws_credentials():
    """Validate AWS credentials by making a simple API call."""
    # Check if we're in local development mode
    is_local = os.environ.get('SQS_ENDPOINT_URL') is not None
    
    if is_local:
        logger.info("Local development mode detected - skipping AWS credential validation")
        return True
        
    try:
        # Test STS to get caller identity
        sts = boto3.client('sts', config=boto_config)
        identity = sts.get_caller_identity()
        logger.info(
            f"AWS credentials validated. Account: {identity.get('Account')}, "
            f"User/Role: {identity.get('Arn')}"
        )
        return True
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(
            f"AWS credential validation failed: {error_code} - {e}"
        )
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating AWS credentials: {e}")
        return False


# === CloudWatch Metrics Helper ===
def send_cloudwatch_metrics(metric_data, max_retries=3):
    """Send metrics to CloudWatch with retry logic and error handling."""
    # Check if we're in local development mode
    is_local = os.environ.get('SQS_ENDPOINT_URL') is not None
    
    if is_local:
        logger.debug(f"Local development mode - skipping CloudWatch metrics: {len(metric_data)} metrics")
        return True
    
    for attempt in range(max_retries):
        try:
            cloudwatch.put_metric_data(
                Namespace="VideoProcessor",
                MetricData=metric_data
            )
            logger.debug(
                f"Successfully sent {len(metric_data)} metrics to CloudWatch"
            )
            return True
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ['InvalidClientTokenId', 'UnauthorizedOperation', 'AccessDenied']:
                logger.warning(
                    f"AWS credentials issue on attempt {attempt + 1}: {error_code}"
                )
                if attempt < max_retries - 1:
                    # Wait longer between retries for credential issues
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(
                        f"Failed to send metrics after {max_retries} attempts: {e}"
                    )
                    return False
            else:
                logger.error(f"CloudWatch error: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error sending metrics: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False
    return False


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
                send_cloudwatch_metrics([
                    {
                        "MetricName": "VideoProcessingErrors",
                        "Value": 1,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "ErrorType", "Value": "FileNotFound"},
                            {"Name": "VideoId", "Value": video_id}
                        ]
                    }
                ])
                return
            else:
                raise

        # Process the single video file
        if not s3_key.endswith(".mp4"):
            logger.warning(f"Skipping non-MP4 file: {s3_key}")
            # Send metric for unsupported file type
            send_cloudwatch_metrics([
                {
                    "MetricName": "VideoProcessingErrors",
                    "Value": 1,
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "ErrorType", 
                         "Value": "UnsupportedFileType"},
                        {"Name": "VideoId", "Value": video_id}
                    ]
                }
            ])
            return

        logger.info(f"Processing: s3://{S3_BUCKET}/{s3_key}")
        local_path = Path("/tmp") / Path(s3_key).name
        
        try:
            # Download video file
            download_start = time.time()
            s3.download_file(S3_BUCKET, s3_key, str(local_path))
            download_time = time.time() - download_start
            logger.info(
                f"Downloaded {s3_key} to {local_path} in {download_time:.2f}s"
            )

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
            send_cloudwatch_metrics([
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
            ])
            
            # Clean up local files
            local_path.unlink(missing_ok=True)
            Path(embedding_path).unlink(missing_ok=True)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing {s3_key}: {str(e)}")
            
            # Send error metrics
            send_cloudwatch_metrics([
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
            ])
            raise
                
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing message: {str(e)}")
        
        # Send general error metric
        send_cloudwatch_metrics([
            {
                "MetricName": "VideoProcessingErrors",
                "Value": 1,
                "Unit": "Count",
                "Dimensions": [
                    {"Name": "ErrorType", "Value": "GeneralError"},
                    {"Name": "VideoId", "Value": video_id or "unknown"}
                ]
            }
        ])
        raise


# === Main loop ===
def run_worker():
    """Main worker loop that continuously polls SQS for messages"""
    logger.info("Starting video processor worker...")
    
    # Validate AWS credentials on startup
    if not validate_aws_credentials():
        logger.error("AWS credentials validation failed. Exiting...")
        return
    
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
