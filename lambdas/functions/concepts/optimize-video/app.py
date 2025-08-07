"""
Lambda function to optimize videos for streaming by adding fast start (moov atom at beginning).
This function is triggered after video upload to ensure videos can be streamed properly.
"""

import boto3
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Configure logging
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

def optimize_video_for_streaming(input_path: Path, output_path: Path) -> bool:
    """
    Re-encode video to H.264 with fast start for streaming compatibility.
    This ensures browser compatibility (Chrome, Safari, Firefox, etc.).
    
    Args:
        input_path: Path to input video file
        output_path: Path to output optimized video file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use ffmpeg to re-encode to H.264 with fast start
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',  # Re-encode to H.264 for browser compatibility
            '-preset', 'fast',  # Fast encoding preset
            '-crf', '23',  # Constant rate factor for good quality
            '-c:a', 'copy',  # Copy audio stream without re-encoding
            '-movflags', '+faststart',  # Move moov atom to beginning
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
        
        logger.info(f"✅ Video optimized: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error optimizing video: {e}")
        return False

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler to optimize videos for streaming.
    
    Expected event structure:
    {
        "s3_bucket": "bucket-name",
        "s3_key": "path/to/video.mp4"
    }
    """
    try:
        # Extract parameters
        s3_bucket = event.get('s3_bucket')
        s3_key = event.get('s3_key')
        
        if not s3_bucket or not s3_key:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing s3_bucket or s3_key'})
            }
        
        logger.info(f"Optimizing video: s3://{s3_bucket}/{s3_key}")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download original video
            input_path = temp_path / "original.mp4"
            logger.info(f"📥 Downloading: s3://{s3_bucket}/{s3_key}")
            s3_client.download_file(s3_bucket, s3_key, str(input_path))
            
            # Check if file exists and has content
            if not input_path.exists() or input_path.stat().st_size == 0:
                logger.error("Downloaded file is empty or doesn't exist")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Downloaded file is empty'})
                }
            
            # Optimize video
            output_path = temp_path / "optimized.mp4"
            if not optimize_video_for_streaming(input_path, output_path):
                logger.error("Failed to optimize video")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Failed to optimize video'})
                }
            
            # Check file sizes
            original_size = input_path.stat().st_size
            optimized_size = output_path.stat().st_size
            logger.info(f"📊 Original size: {original_size:,} bytes")
            logger.info(f"📊 Optimized size: {optimized_size:,} bytes")
            
            # Upload optimized video back to S3
            logger.info(f"📤 Uploading optimized video: s3://{s3_bucket}/{s3_key}")
            s3_client.upload_file(
                str(output_path), 
                s3_bucket, 
                s3_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )
            
            logger.info(f"✅ Successfully optimized: s3://{s3_bucket}/{s3_key}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Video optimized successfully',
                    's3_bucket': s3_bucket,
                    's3_key': s3_key,
                    'original_size': original_size,
                    'optimized_size': optimized_size
                })
            }
            
    except Exception as e:
        logger.error(f"❌ Error processing video: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 