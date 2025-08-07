import os
import boto3
from urllib.parse import unquote
from botocore.exceptions import ClientError

# Add the shared path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from valthera_core import (
    get_user_id_from_event,
    error_response
)


def lambda_handler(event, context):
    """Proxy function to serve videos directly from S3"""

    try:
        # Get video ID from path parameters (using proxy+ to capture full path)
        video_id = event.get('pathParameters', {}).get('proxy')
        print(f"Raw proxy parameter: {video_id}")
        if not video_id:
            return error_response('Video ID is required', 400)

        # Try to decode as base64 first, then URL decode
        try:
            import base64
            # Try base64 decode first
            decoded_bytes = base64.b64decode(video_id)
            video_id = decoded_bytes.decode('utf-8')
            print(f"Base64 decoded video ID: {video_id}")
            # URL decode the result since base64 might contain URL-encoded characters
            video_id = unquote(video_id)
            print(f"URL decoded video ID: {video_id}")
        except Exception as e:
            print(f"Not base64 encoded, using as-is: {e}")
            # URL decode the video ID
            video_id = unquote(video_id)
        
        print(f"Final video ID: {video_id}")
        print(f"Video ID length: {len(video_id)}")

        # Check if we're running locally
        is_local = (os.environ.get('AWS_ENDPOINT_URL') or 
                    os.environ.get('AWS_SAM_LOCAL'))
        
        # For production, require authentication
        if not is_local:
            user_id = get_user_id_from_event(event)
            if not user_id:
                return error_response(
                    'User not authenticated', 401, 'UNAUTHORIZED'
                )
            print(f"Authenticated user: {user_id}")
        else:
            print("Local development - bypassing authentication")

        # Configure S3 client
        if is_local:
            # Local development - use LocalStack
            s3_endpoint = os.environ.get('S3_ENDPOINT_URL',
                                       'http://localhost:4566')
            bucket_name = os.environ.get('VIDEO_BUCKET_NAME',
                                      'valthera-dev-videos-local')
            
            # For Lambda running in Docker container, use host.docker.internal
            if s3_endpoint and 'localhost' in s3_endpoint:
                s3_endpoint = s3_endpoint.replace('localhost',
                                               'host.docker.internal')
            
            s3_client = boto3.client(
                's3',
                endpoint_url=s3_endpoint,
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
        else:
            # Production - use real AWS S3
            bucket_name = os.environ.get('VIDEO_BUCKET_NAME')
            s3_client = boto3.client('s3', region_name='us-east-1')
        
        print(f"Using S3 endpoint: {s3_endpoint if is_local else 'AWS S3'}")
        print(f"Using bucket: {bucket_name}")

        try:
            # Get the video object from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=video_id)
            video_content = response['Body'].read()
            content_type = response.get('ContentType', 'video/mp4')

            print(f"Successfully retrieved video: {video_id}")
            print(f"Content type: {content_type}")
            print(f"Content length: {len(video_content)} bytes")

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': content_type,
                    'Content-Length': str(len(video_content)),
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Cache-Control': 'public, max-age=3600'
                },
                'body': video_content,
                'isBase64Encoded': True
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                print(f"Video not found: {video_id}")
                return error_response('Video not found', 404)
            else:
                print(f"S3 error: {e}")
                return error_response('Failed to retrieve video', 500)

    except Exception as e:
        print(f"Unexpected error: {e}")
        return error_response('Internal server error', 500) 