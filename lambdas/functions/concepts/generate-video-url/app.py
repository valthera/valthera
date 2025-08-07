import boto3
import sys
import os
import urllib.parse
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    success_response, 
    error_response, 
    get_user_id_from_event,
    Config
)


@log_execution_time
def lambda_handler(event, context):
    """Generate presigned download URLs for videos."""
    try:
        log_request_info(event)
        
        # Get video ID from path parameters and URL decode it
        video_id = event.get('pathParameters', {}).get('videoId')
        if not video_id:
            return error_response('Video ID is required', 400)
        
        # URL decode the video ID since it's an S3 key
        try:
            decoded_video_id = urllib.parse.unquote(video_id)
            print(f"Original video_id: {video_id}")
            print(f"Decoded video_id: {decoded_video_id}")            
        except Exception as e:
            print(f"Error decoding video_id: {str(e)}")
            decoded_video_id = video_id
        
        # Check if we're running locally
        is_local = (os.environ.get('AWS_ENDPOINT_URL') or 
                    os.environ.get('AWS_SAM_LOCAL'))
        
        if is_local:
            print("Local development detected - bypassing authentication and "
                  "using direct S3 URLs")
            
            # For local development, return a direct S3 URL without authentication
            s3_endpoint = os.environ.get('S3_ENDPOINT_URL', 
                                        'http://localhost:4566')
            bucket_name = os.environ.get('VIDEO_BUCKET_NAME', 
                                       'valthera-dev-videos-local')
            
            # Create direct URL for local S3
            direct_url = f"{s3_endpoint}/{bucket_name}/{decoded_video_id}"
            
            # Extract filename from S3 key
            filename = (decoded_video_id.split('/')[-1] 
                       if '/' in decoded_video_id else decoded_video_id)
            
            # Return direct URL for local development
            response_data = {
                'downloadUrl': direct_url,
                'videoId': video_id,
                's3Key': decoded_video_id,
                'fileName': filename,
                'fileSize': 0,  # We don't check file size in local dev
                'metadata': {},
                'expires': datetime.utcnow().isoformat() + '+01:00',
                'isLocal': True
            }
            
            response = success_response(response_data, 200)
            log_response_info(response)
            return response
        
        # For production, require authentication
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        
        if not user_id:
            return error_response(
                'User not authenticated', 401, 'UNAUTHORIZED'
            )
        
        # The video_id is actually the S3 key
        s3_key = decoded_video_id
        print(f"Using S3 key: {s3_key}")
        
        # Generate presigned download URL using Lambda execution role credentials
        # Force use of Lambda execution role by not passing any credentials
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Check if the file exists and get metadata
        try:
            head_response = s3_client.head_object(
                Bucket=Config.VIDEO_BUCKET,
                Key=s3_key
            )
            file_size = head_response.get('ContentLength', 0)
            metadata = head_response.get('Metadata', {})
            print(f"File exists: {s3_key}, size: {file_size}")
        except s3_client.exceptions.NoSuchKey:
            print(f"File not found: {s3_key}")
            return error_response(f'Video file not found: {s3_key}', 404)
        except Exception as e:
            print(f"Error checking file: {str(e)}")
            log_error(e, {'function': 'generate_video_url', 
                         'operation': 'head_object', 's3_key': s3_key})
            return error_response('Error checking video file', 500)
        
        # Extract filename from S3 key
        filename = s3_key.split('/')[-1] if '/' in s3_key else s3_key
        
        # Generate presigned URL (expires in 24 hours for better user experience)
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': Config.VIDEO_BUCKET,
                    'Key': s3_key
                },
                ExpiresIn=86400  # 24 hours
            )
            print(f"Generated presigned URL for {s3_key}: "
                  f"{presigned_url[:100]}...")
        except Exception as e:
            print(f"Error generating presigned URL: {str(e)}")
            log_error(e, {'function': 'generate_video_url', 
                         'operation': 'generate_presigned_url', 
                         's3_key': s3_key})
            return error_response('Error generating video URL', 500)
        
        # Return presigned URL data
        response_data = {
            'downloadUrl': presigned_url,
            'videoId': video_id,
            's3Key': s3_key,
            'fileName': filename,
            'fileSize': file_size,
            'metadata': metadata,
            'expires': datetime.utcnow().isoformat() + '+01:00'  # 24 hours
        }
        
        response = success_response(response_data, 200)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'generate_video_url', 'event': event})
        return error_response('Internal server error', 500) 