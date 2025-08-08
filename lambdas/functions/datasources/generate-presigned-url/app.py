import json
import boto3
import uuid
from datetime import datetime
import sys
import os
import base64
from valthera_core import (
    get_user_id_from_event,
    get_dynamodb_resource,
    get_s3_client,
    success_response,
    error_response,
    not_found_response,
    Config
)
# Remove valthera_core imports and implement functions directly
def log_execution_time(func):
    """Decorator to log function execution time."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def log_request_info(event):
    """Log request information."""
    print(f"Request method: {event.get('httpMethod')}")
    print(f"Request path: {event.get('path')}")
    print(f"Request headers: {event.get('headers')}")
    print(f"Request body: {event.get('body')}")

def log_error(error, context=None):
    """Log error information."""
    print(f"ERROR: {error}")
    if context:
        print(f"Context: {context}")

def log_response_info(response):
    """Log response information."""
    print(f"Response: {response}")

## Use shared response helpers

def validate_file_type(filename):
    """Validate file type based on extension."""
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    file_extension = os.path.splitext(filename.lower())[1]
    
    if not file_extension:
        return False, 'File must have a valid extension'
    
    if file_extension not in allowed_extensions:
        return False, f'File type {file_extension} is not supported. Allowed types: {", ".join(allowed_extensions)}'
    
    return True, None

def decode_jwt_payload(token):
    """Decode JWT token payload without verification (for local development)."""
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode from base64
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None

def lambda_handler(event, context):
    """Generate presigned URLs for secure file uploads to S3."""
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
        filename = data.get('filename')
        content_type = data.get('contentType')
        file_size = data.get('fileSize', 0)
        
        if not filename:
            return error_response('filename is required', 400)
        
        # Validate file type
        is_valid_type, type_error = validate_file_type(filename)
        if not is_valid_type:
            return error_response(type_error, 400, 'VALIDATION_ERROR')
        
        # Validate file size (max 100MB)
        max_size = Config.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        if file_size > max_size:
            return error_response(f'File size exceeds maximum allowed size of {Config.MAX_FILE_SIZE_MB}MB', 400, 'VALIDATION_ERROR')
        
        # Verify data source exists and belongs to user
        dynamodb = get_dynamodb_resource()
        
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"Table name: {table_name}")
        table = dynamodb.Table(table_name)
        
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Data source', datasource_id)
        
        # Generate unique file ID and S3 key
        file_id = str(uuid.uuid4())
        s3_key = f"users/{user_id}/data-sources/{datasource_id}/{file_id}_{filename}"
        
        # Generate presigned URL for upload
        s3_client = get_s3_client()
        
        # Set conditions for the presigned URL
        conditions = [
            ["content-length-range", 1, max_size],  # File size limits
        ]
        
        if content_type:
            conditions.append(["eq", "$Content-Type", content_type])
        
        # Generate presigned URL (expires in 1 hour)
        presigned_data = s3_client.generate_presigned_post(
            Bucket=Config.VIDEO_BUCKET,
            Key=s3_key,
            Fields={
                'Content-Type': content_type or 'application/octet-stream'
            },
            Conditions=conditions,
            ExpiresIn=3600  # 1 hour
        )
        
        # Return presigned URL data
        response_data = {
            'fileId': file_id,
            'uploadUrl': presigned_data['url'],
            'fields': presigned_data['fields'],
            's3Key': s3_key,
            'expires': datetime.utcnow().isoformat() + '+01:00'  # 1 hour from now
        }
        
        response = success_response(response_data, 200)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'generate_presigned_url', 'event': event})
        return error_response('Internal server error', 500)