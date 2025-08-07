import json
import boto3
import uuid
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    validate_file_type,
    success_response, 
    error_response, 
    not_found_response,
    get_user_id_from_event,
    Config
)


@log_execution_time
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
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        print(f"AWS_ENDPOINT_URL: {aws_endpoint_url}")
        
        if aws_endpoint_url:
            # For Docker containers, use host.docker.internal to connect to host
            if aws_endpoint_url.startswith('http://localhost:'):
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
            dynamodb = boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
        else:
            dynamodb = boto3.resource('dynamodb')
        
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
        s3_kwargs = {}
        if Config.S3_ENDPOINT_URL:
            s3_kwargs['endpoint_url'] = Config.S3_ENDPOINT_URL
            s3_kwargs['region_name'] = 'us-east-1'
        
        s3_client = boto3.client('s3', **s3_kwargs)
        
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