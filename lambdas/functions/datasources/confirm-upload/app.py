import json
import boto3
import base64
import subprocess
import tempfile
import os
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info
)
from valthera_core import success_response, error_response, not_found_response
from valthera_core import Config


# Configuration for video processing
MAX_LAMBDA_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB - Lambda temp storage limit
VIDEO_OPTIMIZATION_ENABLED = True  # Can be controlled via environment variable


def should_optimize_video(file_size, file_type):
    """Determine if video should be optimized in Lambda."""
    if not VIDEO_OPTIMIZATION_ENABLED:
        return False
    
    # Only process video files
    if not file_type.startswith('video/'):
        return False
    
    # Only process files small enough for Lambda
    if file_size > MAX_LAMBDA_VIDEO_SIZE:
        return False
    
    return True


def optimize_video_in_lambda(s3_key, file_size):
    """Optimize video for Chrome compatibility using FFmpeg in Lambda."""
    try:
        s3_client = boto3.client('s3')
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download video from S3
            input_path = temp_path / "original.mp4"
            print(f"📥 Downloading: s3://{Config.VIDEO_BUCKET}/{s3_key}")
            s3_client.download_file(Config.VIDEO_BUCKET, s3_key, str(input_path))
            
            # Check if file exists and has content
            if not input_path.exists() or input_path.stat().st_size == 0:
                raise Exception("Downloaded file is empty or doesn't exist")
            
            # Optimize video for Chrome compatibility
            output_path = temp_path / "optimized.mp4"
            if not optimize_video_for_chrome(input_path, output_path):
                raise Exception("Failed to optimize video")
            
            # Check file sizes
            original_size = input_path.stat().st_size
            optimized_size = output_path.stat().st_size
            print(f"📊 Original size: {original_size:,} bytes")
            print(f"📊 Optimized size: {optimized_size:,} bytes")
            
            # Upload optimized video back to S3
            print(f"📤 Uploading optimized video: s3://{Config.VIDEO_BUCKET}/{s3_key}")
            s3_client.upload_file(
                str(output_path), 
                Config.VIDEO_BUCKET, 
                s3_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'Metadata': {
                        'chrome-optimized': 'true',
                        'original-size': str(original_size),
                        'optimized-size': str(optimized_size),
                        'optimization-date': datetime.utcnow().isoformat()
                    }
                }
            )
            
            print(f"✅ Successfully optimized: s3://{Config.VIDEO_BUCKET}/{s3_key}")
            return True
            
    except Exception as e:
        print(f"❌ Error optimizing video in Lambda: {e}")
        log_error(e, {'function': 'optimize_video_in_lambda', 's3_key': s3_key})
        return False


def optimize_video_for_chrome(input_path, output_path):
    """Optimize video for Chrome compatibility using FFmpeg."""
    try:
        # Use ffmpeg to re-encode to H.264 with Chrome-compatible settings
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',  # Re-encode to H.264 for browser compatibility
            '-preset', 'fast',  # Fast encoding preset for Lambda
            '-crf', '23',  # Constant rate factor for good quality
            '-profile:v', 'baseline',  # Baseline profile for maximum compatibility
            '-level', '3.1',  # Level 3.1 for broad device support
            '-pix_fmt', 'yuv420p',  # Standard pixel format
            '-c:a', 'aac',  # Re-encode audio to AAC
            '-b:a', '128k',  # Audio bitrate
            '-movflags', '+faststart',  # Move moov atom to beginning for streaming
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        print(f"🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
        
        print(f"✅ Video optimized for Chrome: {output_path}")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg processing timed out")
        return False
    except Exception as e:
        print(f"❌ Error optimizing video: {e}")
        return False


def trigger_async_optimization(s3_key, user_id, datasource_id):
    """Trigger async video optimization via SQS."""
    try:
        sqs_client = boto3.client('sqs')
        
        message_body = {
            's3_key': s3_key,
            'bucket': Config.VIDEO_BUCKET,
            'user_id': user_id,
            'datasource_id': datasource_id,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'video_optimization'
        }
        
        # Send to SQS queue for async processing
        sqs_client.send_message(
            QueueUrl=Config.VIDEO_OPTIMIZATION_QUEUE,
            MessageBody=json.dumps(message_body)
        )
        
        print(f"✅ Triggered async optimization for: {s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Error triggering async optimization: {e}")
        log_error(e, {'function': 'trigger_async_optimization', 's3_key': s3_key})
        return False


@log_execution_time
def lambda_handler(event, context):
    """Confirm file upload completion and optionally optimize video for Chrome compatibility."""
    try:
        log_request_info(event)
        
        # Get data source ID from path parameters  
        datasource_id = event.get('pathParameters', {}).get('datasourceId')
        if not datasource_id:
            return error_response('Data source ID is required', 400)
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Parse request body
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        
        # Validate required fields
        file_id = data.get('fileId')
        filename = data.get('filename')
        s3_key = data.get('s3Key')
        
        if not all([file_id, filename, s3_key]):
            return error_response('fileId, filename, and s3Key are required', 400)
        
        # Verify the S3 key follows the expected pattern for this user/datasource
        expected_prefix = f"users/{user_id}/data-sources/{datasource_id}/"
        if not s3_key.startswith(expected_prefix):
            return error_response('Invalid S3 key for this data source', 400)
        
        # Verify file exists in S3
        s3_client = boto3.client('s3')
        try:
            head_response = s3_client.head_object(Bucket=Config.VIDEO_BUCKET, Key=s3_key)
            file_size = head_response['ContentLength']
            content_type = head_response.get('ContentType', 'application/octet-stream')
            last_modified = head_response['LastModified'].isoformat()
        except s3_client.exceptions.NoSuchKey:
            return error_response('File not found in S3', 404)
        except Exception as e:
            log_error(e, {'function': 'confirm_upload', 's3_key': s3_key})
            return error_response('Failed to verify file in S3', 500)
        
        # Determine processing status based on video optimization
        processing_status = 'completed'
        optimization_metadata = {}
        
        # Check if video should be optimized
        if should_optimize_video(file_size, content_type):
            print(f"🎬 Video optimization needed: {filename} ({file_size:,} bytes)")
            
            # Try to optimize in Lambda (for small videos)
            if file_size <= MAX_LAMBDA_VIDEO_SIZE:
                print("🔄 Attempting Lambda optimization...")
                if optimize_video_in_lambda(s3_key, file_size):
                    processing_status = 'optimized'
                    optimization_metadata = {
                        'optimization_method': 'lambda',
                        'optimization_date': datetime.utcnow().isoformat()
                    }
                else:
                    # Fallback to async processing
                    print("⚠️ Lambda optimization failed, triggering async processing...")
                    trigger_async_optimization(s3_key, user_id, datasource_id)
                    processing_status = 'pending_optimization'
                    optimization_metadata = {
                        'optimization_method': 'async',
                        'optimization_triggered': datetime.utcnow().isoformat()
                    }
            else:
                # Large video - use async processing
                print("📤 Large video detected, triggering async optimization...")
                trigger_async_optimization(s3_key, user_id, datasource_id)
                processing_status = 'pending_optimization'
                optimization_metadata = {
                    'optimization_method': 'async',
                    'optimization_triggered': datetime.utcnow().isoformat()
                }
        else:
            print(f"✅ No optimization needed for: {filename}")
        
        # Get data source from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Data source', datasource_id)
        
        datasource = response['Item']
        
        # Create file metadata
        file_metadata = {
            'id': file_id,
            'fileName': filename,
            'fileSize': file_size,
            'uploadDate': datetime.utcnow().isoformat(),
            's3Key': s3_key,
            'processingStatus': processing_status,
            'lastModified': last_modified,
            'contentType': content_type,
            'optimization': optimization_metadata,
            'metadata': {
                'width': None,  # Will be extracted during processing if needed
                'height': None,
                'fps': None,
                'format': filename.split('.')[-1] if '.' in filename else 'unknown'
            }
        }
        
        # Update data source with new file
        files = datasource.get('files', [])
        files.append(file_metadata)
        
        # Update DynamoDB
        table.update_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            },
            UpdateExpression='SET files = :files, videoCount = :videoCount, totalSize = :totalSize, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':files': files,
                ':videoCount': len(files),
                ':totalSize': sum(f.get('fileSize', 0) for f in files),
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        # Return success response with file metadata
        response = success_response(file_metadata, 200)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'confirm_upload_enhanced', 'event': event})
        return error_response('Internal server error', 500)


def get_user_id_from_event(event):
    """Extract user ID from Cognito authorizer context or JWT token."""
    try:
        # Get user ID from Cognito authorizer (if available)
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        user_id = authorizer_context.get('sub') or authorizer_context.get('user_id')
        
        if not user_id:
            # Try to extract from Authorization header JWT token
            headers = event.get('headers', {})
            auth_header = headers.get('Authorization') or headers.get('authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    # Decode JWT payload (without verification for now since we don't have the key)
                    # JWT format: header.payload.signature
                    payload_encoded = token.split('.')[1]
                    # Add padding if needed
                    padding = 4 - len(payload_encoded) % 4
                    if padding != 4:
                        payload_encoded += '=' * padding
                    
                    payload_bytes = base64.b64decode(payload_encoded)
                    payload = json.loads(payload_bytes.decode('utf-8'))
                    
                    # Extract user ID from JWT payload
                    user_id = payload.get('sub') or payload.get('user_id') or payload.get('username')
                    
                except Exception as jwt_error:
                    log_error(jwt_error, {'function': 'jwt_decode', 'token_preview': token[:50]})
        
        if not user_id:
            # Fallback to headers if authorizer not available
            user_id = event.get('headers', {}).get('X-User-ID')
        
        return user_id
    except Exception as e:
        log_error(e, {'function': 'get_user_id_from_event'})
        return None 