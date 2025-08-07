import boto3
import sys
import os
import urllib.parse
import base64
import json
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
    """Stream video content directly from S3."""
    try:
        log_request_info(event)
        
        # Get video ID from path parameters and URL decode it
        video_id = event.get('pathParameters', {}).get('videoId')
        if not video_id:
            return error_response('Video ID is required', 400)
        
        # URL decode the video ID (since it's actually an S3 key)
        video_id = urllib.parse.unquote(video_id)
        
        # Check if we're running locally
        is_local = (os.environ.get('AWS_ENDPOINT_URL') or 
                   os.environ.get('AWS_SAM_LOCAL'))
        
        # For production, require authentication
        if not is_local:
            # Get user ID from Cognito authorizer or token query parameter
            user_id = get_user_id_from_event(event)
            
            # If no user from authorizer, try to get from token query parameter
            if not user_id:
                query_params = event.get('queryStringParameters') or {}
                token = query_params.get('token')
                
                if token:
                    try:
                        # Decode JWT token manually (without verification for simplicity)
                        # JWT format: header.payload.signature
                        parts = token.split('.')
                        if len(parts) >= 2:
                            # Decode the payload (second part)
                            payload = parts[1]
                            # Add padding if needed
                            payload += '=' * (4 - len(payload) % 4)
                            decoded_bytes = base64.b64decode(payload)
                            decoded = json.loads(decoded_bytes.decode('utf-8'))
                            user_id = decoded.get('sub') or decoded.get('cognito:username')
                            print(f"User ID from token: {user_id}")
                    except Exception as e:
                        print(f"Error decoding token: {str(e)}")
                
                if not user_id:
                    return error_response(
                        'User not authenticated', 401, 'UNAUTHORIZED'
                    )
        else:
            print("Local development - bypassing authentication")
        
        # The video_id is actually the S3 key
        s3_key = video_id
        
        # Configure S3 client based on environment
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
            bucket_name = Config.VIDEO_BUCKET
            s3_client = boto3.client('s3', region_name='us-east-1')
        
        print(f"Using S3 endpoint: {s3_endpoint if is_local else 'AWS S3'}")
        print(f"Using bucket: {bucket_name}")
        
        # Check if the file exists and get metadata
        try:
            head_response = s3_client.head_object(
                Bucket=bucket_name,
                Key=s3_key
            )
            file_size = head_response.get('ContentLength', 0)
            content_type = head_response.get('ContentType', 'video/mp4')
            print(f"Streaming file: {s3_key}, size: {file_size}")
        except s3_client.exceptions.NoSuchKey:
            print(f"File not found: {s3_key}")
            return error_response(f'Video file not found: {s3_key}', 404)
        except Exception as e:
            print(f"Error checking file: {str(e)}")
            log_error(e, {'function': 'stream_video', 'operation': 'head_object', 's3_key': s3_key})
            return error_response('Error checking video file', 500)
        
        # Handle HEAD requests (for browser preflight checks)
        if event.get('httpMethod') == 'HEAD':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': content_type,
                    'Content-Length': str(file_size),
                    'Accept-Ranges': 'bytes',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Range',
                    'Cache-Control': 'public, max-age=31536000'
                },
                'body': ''
            }
        
        # Handle range requests for video streaming
        range_header = event.get('headers', {}).get('Range') or event.get('headers', {}).get('range')
        
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            # Ensure end doesn't exceed file size
            end = min(end, file_size - 1)
            content_length = end - start + 1
            
            try:
                # Get partial object from S3
                s3_response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Range=f'bytes={start}-{end}'
                )
                
                # Read the content
                video_content = s3_response['Body'].read()
                
                # Return partial content response
                response = {
                    'statusCode': 206,  # Partial Content
                    'headers': {
                        'Content-Type': content_type,
                        'Content-Length': str(content_length),
                        'Content-Range': f'bytes {start}-{end}/{file_size}',
                        'Accept-Ranges': 'bytes',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Range',
                        'Cache-Control': 'public, max-age=31536000'
                    },
                    'body': base64.b64encode(video_content).decode('utf-8'),
                    'isBase64Encoded': True
                }
                
                print(f"Streaming range {start}-{end} of {file_size} bytes")
                return response
                
            except Exception as e:
                print(f"Error streaming video range: {str(e)}")
                log_error(e, {'function': 'stream_video', 'operation': 'get_object_range', 's3_key': s3_key})
                return error_response('Error streaming video', 500)
        
        else:
            # No range header - stream entire file (for small files)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                # For large files, return range request required
                return {
                    'statusCode': 416,  # Range Not Satisfiable
                    'headers': {
                        'Content-Type': 'text/plain',
                        'Content-Range': f'bytes */{file_size}',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': 'Range header required for large files'
                }
            
            try:
                # Get entire object from S3
                s3_response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key=s3_key
                )
                
                # Read the content
                video_content = s3_response['Body'].read()
                
                # Return full content response
                response = {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': content_type,
                        'Content-Length': str(file_size),
                        'Accept-Ranges': 'bytes',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Range',
                        'Cache-Control': 'public, max-age=31536000'
                    },
                    'body': base64.b64encode(video_content).decode('utf-8'),
                    'isBase64Encoded': True
                }
                
                print(f"Streaming entire file: {file_size} bytes")
                return response
                
            except Exception as e:
                print(f"Error streaming entire video: {str(e)}")
                log_error(e, {'function': 'stream_video', 'operation': 'get_object_full', 's3_key': s3_key})
                return error_response('Error streaming video', 500)
        
    except Exception as e:
        log_error(e, {'function': 'stream_video', 'event': event})
        return error_response('Internal server error', 500)