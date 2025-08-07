import os
import json
import boto3
import time
import logging
from pathlib import Path
import botocore.exceptions
from datetime import datetime

import cv2
import numpy as np
import torch
import sys

# Add V-JEPA wrapper to path
sys.path.append('/opt/vjepa')

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
logging.basicConfig(
    level=logging.INFO,
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
# Use centralized SQS client if available, otherwise fallback to direct boto3
if USE_VALTHERA_CORE:
    sqs = get_sqs_client()
else:
    sqs_kwargs = {'region_name': REGION}
    if os.environ.get('SQS_ENDPOINT_URL'):
        sqs_kwargs['endpoint_url'] = os.environ.get('SQS_ENDPOINT_URL')
    sqs = boto3.client("sqs", **sqs_kwargs)

s3 = boto3.client("s3", region_name=REGION)

# === V-JEPA2 Model ===
vjepa_model = None

def initialize_vjepa():
    """Initialize V-JEPA2 model"""
    global vjepa_model
    try:
        from vjepa_wrapper import get_vjepa_model
        vjepa_model = get_vjepa_model()
        logger.info("✅ V-JEPA2 model initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize V-JEPA2 model: {e}")
        logger.info("Will fallback to mean RGB encoding")
        vjepa_model = None

def upload_startup_log():
    """Upload a startup log to S3 to confirm the worker is starting"""
    try:
        now = datetime.utcnow().isoformat()
        log_content = f"Worker startup log - {now}\n"
        log_content += f"SQS_QUEUE_URL: {SQS_QUEUE_URL}\n"
        log_content += f"S3_BUCKET: {S3_BUCKET}\n"
        log_content += f"AWS_REGION: {REGION}\n"
        
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"logs/worker_startup_{now}.log",
            Body=log_content
        )
        logger.info("✅ Startup log uploaded to S3")
    except Exception as e:
        logger.error(f"❌ Failed to upload startup log: {str(e)}")

# Initialize V-JEPA2 model and upload startup log
initialize_vjepa()
upload_startup_log()

logger.info(
    f"Initialized video processor with SQS: {SQS_QUEUE_URL}, "
    f"S3: {S3_BUCKET}"
)


# === V-JEPA2 embedding logic ===
def generate_embedding(video_path):
    """Generate embeddings from video using V-JEPA2 or fallback to mean RGB"""
    logger.info(f"Generating embeddings for {video_path}")
    
    if vjepa_model is not None:
        return generate_vjepa2_embedding(video_path)
    else:
        logger.warning("V-JEPA2 model not available, using mean RGB fallback")
        return generate_fallback_embedding(video_path)

def generate_vjepa2_embedding(video_path):
    """Generate embeddings using V-JEPA2 model"""
    logger.info(f"Generating V-JEPA2 embeddings for {video_path}")
    
    try:
        cap = cv2.VideoCapture(str(video_path))
        frames = []
        frame_count = 0
        
        # Read all frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB and normalize to [0, 1]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_normalized = frame_rgb.astype(np.float32) / 255.0
            
            # Resize frame to standard size (224x224 for most vision models)
            frame_resized = cv2.resize(frame_normalized, (224, 224))
            
            # Convert to tensor format (C, H, W)
            frame_tensor = torch.from_numpy(frame_resized).permute(2, 0, 1)
            frames.append(frame_tensor)
            frame_count += 1
            
            # Log progress every 100 frames
            if frame_count % 100 == 0:
                logger.info(f"Processed {frame_count} frames")
        
        cap.release()
        
        if not frames:
            logger.warning("No frames found in video")
            return []
        
        # Stack frames into video tensor (T, C, H, W)
        video_tensor = torch.stack(frames)
        logger.info(f"Video tensor shape: {video_tensor.shape}")
        
        # Extract embeddings using V-JEPA2
        embeddings = vjepa_model.extract_embeddings(video_tensor)
        
        logger.info(f"Generated V-JEPA2 embeddings shape: {embeddings.shape}")
        
        # Convert to list for JSON serialization
        if len(embeddings.shape) > 1:
            # If we get multiple embeddings (per frame or segments), flatten or take mean
            embedding_list = np.mean(embeddings, axis=0).tolist()
        else:
            embedding_list = embeddings.tolist()
        
        logger.info(f"Generated V-JEPA2 embeddings for {frame_count} frames")
        return embedding_list
        
    except Exception as e:
        logger.error(f"Error generating V-JEPA2 embeddings: {e}")
        logger.info("Falling back to mean RGB encoding")
        return generate_fallback_embedding(video_path)

def generate_fallback_embedding(video_path):
    """Fallback embedding generation using mean RGB (original method)"""
    logger.info(f"Generating fallback embeddings for {video_path}")
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
    logger.info(f"Generated fallback embeddings for {frame_count} frames")
    return embeddings


# === Process a single job ===
def process_message(msg):
    """Process a single SQS message containing video processing job"""
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
                return
            else:
                raise

        # Process the single video file
        if not s3_key.endswith(".mp4"):
            logger.warning(f"Skipping non-MP4 file: {s3_key}")
            return

        logger.info(f"Processing: s3://{S3_BUCKET}/{s3_key}")
        local_path = Path("/tmp") / Path(s3_key).name
        
        try:
            # Download video file
            s3.download_file(S3_BUCKET, s3_key, str(local_path))
            logger.info(f"Downloaded {s3_key} to {local_path}")

            # Run embedding
            embedding = generate_embedding(local_path)

            # Save embedding locally
            embedding_path = str(local_path).replace(".mp4", ".embedding.json")
            with open(embedding_path, "w") as f:
                json.dump(embedding, f)

            # Upload embedding back to same folder
            output_key = s3_key.replace(".mp4", ".embedding.json")
            s3.upload_file(embedding_path, S3_BUCKET, output_key)

            logger.info(
                f"✅ Successfully processed: s3://{S3_BUCKET}/{output_key}"
            )
            
            # Clean up local files
            local_path.unlink(missing_ok=True)
            Path(embedding_path).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Error processing {s3_key}: {str(e)}")
            raise
                
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
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