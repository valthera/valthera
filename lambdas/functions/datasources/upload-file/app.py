import json
import boto3
import base64
import uuid
import subprocess
import tempfile
from datetime import datetime
import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import valthera_core
sys.path.append(os.path.dirname(__file__))

from valthera_core import (
    log_execution_time,
    log_request_info,
    log_error,
    log_response_info,
    success_response,
    error_response,
    not_found_response,
    get_user_id_from_event,
    validate_file_size,
    validate_file_type,
    get_dynamodb_resource,
    get_s3_client,
    Config
)

# Configuration for video processing
MAX_LAMBDA_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB - Lambda temp storage limit
# Disable video optimization for local development
VIDEO_OPTIMIZATION_ENABLED = False  # Disabled for local development


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


def optimize_video_in_lambda(file_content, file_name):
    """Optimize video for Chrome compatibility using FFmpeg in Lambda."""
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save original video to temp file
            input_path = temp_path / file_name
            with open(input_path, 'wb') as f:
                f.write(file_content)
            
            # Check if file exists and has content
            if not input_path.exists() or input_path.stat().st_size == 0:
                raise Exception("File is empty or doesn't exist")
            
            # Optimize video for Chrome compatibility
            output_path = temp_path / f"optimized_{file_name}"
            if not optimize_video_for_chrome(input_path, output_path):
                raise Exception("Failed to optimize video")
            
            # Check file sizes
            original_size = input_path.stat().st_size
            optimized_size = output_path.stat().st_size
            print(f"📊 Original size: {original_size:,} bytes")
            print(f"📊 Optimized size: {optimized_size:,} bytes")
            
            # Read optimized video content
            with open(output_path, 'rb') as f:
                optimized_content = f.read()
            
            print(f"✅ Successfully optimized video: {file_name}")
            return optimized_content
            
    except Exception as e:
        print(f"❌ Error optimizing video in Lambda: {e}")
        log_error(e, {'function': 'optimize_video_in_lambda', 'file_name': file_name})
        return None


@log_execution_time
def lambda_handler(event, context):
    """Upload a file to a data source."""
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
        
        # Parse request body (JSON with base64 content)
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        try:
            # Parse JSON body
            body_data = json.loads(event['body'])
            file_name = body_data.get('filename', 'unknown')
            base64_content = body_data.get('content', '')
            
            # Decode base64 content
            file_content = base64.b64decode(base64_content)
            file_size = len(file_content)
            
        except json.JSONDecodeError as e:
            return error_response(f'Invalid JSON data: {str(e)}', 400)
        except Exception as e:
            return error_response(f'Invalid file data: {str(e)}', 400)
        
        if not file_content:
            return error_response('No file data found', 400)
        
        # Validate file
        is_valid_size, size_error = validate_file_size(file_size, max_size_mb=100)
        if not is_valid_size:
            return error_response(size_error, 400, 'VALIDATION_ERROR')
        
        # Validate file type
        is_valid_type, type_error = validate_file_type(file_name, allowed_extensions=['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'])
        if not is_valid_type:
            return error_response(type_error, 400, 'VALIDATION_ERROR')
        
        # Determine content type
        content_type = 'video/mp4'  # Default for video files
        if file_name.lower().endswith('.avi'):
            content_type = 'video/avi'
        elif file_name.lower().endswith('.mov'):
            content_type = 'video/quicktime'
        elif file_name.lower().endswith('.mkv'):
            content_type = 'video/x-matroska'
        
        # Determine processing status and optimize video if needed
        processing_status = 'completed'
        optimization_metadata = {}
        final_content = file_content
        final_size = file_size
        
        # Check if video should be optimized
        if should_optimize_video(file_size, content_type):
            print(f"🎬 Video optimization needed: {file_name} ({file_size:,} bytes)")
            
            if file_size <= MAX_LAMBDA_VIDEO_SIZE:
                print("🔄 Attempting Lambda optimization...")
                optimized_content = optimize_video_in_lambda(file_content, file_name)
                
                if optimized_content:
                    final_content = optimized_content
                    final_size = len(optimized_content)
                    processing_status = 'optimized'
                    optimization_metadata = {
                        'optimization_method': 'lambda',
                        'optimization_date': datetime.utcnow().isoformat()
                    }
                    print(f"✅ Video optimized successfully")
                else:
                    print("⚠️ Lambda optimization failed, keeping original video")
                    optimization_metadata = {
                        'optimization_method': 'failed',
                        'optimization_attempted': datetime.utcnow().isoformat()
                    }
            else:
                print("📤 Large video detected, skipping optimization")
                optimization_metadata = {
                    'optimization_method': 'skipped',
                    'reason': 'file_too_large',
                    'max_size': MAX_LAMBDA_VIDEO_SIZE
                }
        else:
            print(f"✅ No optimization needed for: {file_name}")
        
        # Get data source from DynamoDB
        dynamodb = get_dynamodb_resource()
        
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"Table name: {table_name}")
        table = dynamodb.Table(table_name)
        
        # Check if data source exists and belongs to user
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Data source', datasource_id)
        
        datasource = response['Item']
        
        # Generate S3 key with user-scoped organization
        file_id = str(uuid.uuid4())
        s3_key = f"users/{user_id}/data-sources/{datasource_id}/{file_id}_{file_name}"
        
        # Upload to S3 (with optimized content if available)
        s3 = get_s3_client()
        
        bucket_name = os.environ.get('VIDEO_BUCKET_NAME', 'valthera-dev-videos')
        print(f"S3 bucket: {bucket_name}")
        if Config.S3_ENDPOINT_URL:
            # In our local stack, video uploads go to 'valthera-dev-videos-local'
            bucket_name = 'valthera-dev-videos-local'
            print(f"Using local bucket name: {bucket_name}")
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=final_content,
            ContentType=content_type,
            Metadata={
                'chrome-optimized': str(processing_status == 'optimized').lower(),
                'original-size': str(file_size),
                'final-size': str(final_size),
                'optimization-date': datetime.utcnow().isoformat()
            }
        )
        
        # Create file metadata
        file_metadata = {
            'fileName': file_name,
            'fileSize': final_size,
            'uploadDate': datetime.utcnow().isoformat(),
            's3Key': s3_key,
            'processingStatus': processing_status,
            'contentType': content_type,
            'optimization': optimization_metadata,
            'metadata': {
                'width': None,  # Will be extracted during processing if needed
                'height': None,
                'fps': None,
                'format': file_name.split('.')[-1] if '.' in file_name else 'unknown'
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
        
        # Return success response
        response_data = {
            'id': file_id,
            'fileName': file_name,
            'fileSize': final_size,
            'uploadDate': file_metadata['uploadDate'],
            's3Key': s3_key,
            'processingStatus': processing_status,
            'contentType': content_type,
            'optimization': optimization_metadata,
            'metadata': file_metadata['metadata']
        }
        
        response = success_response(response_data, 201)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'upload_file', 'event': event})
        return error_response('Internal server error', 500) 