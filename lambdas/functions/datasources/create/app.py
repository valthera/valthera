import json
import boto3
import uuid
import base64
from datetime import datetime
import sys
import os

# Add the current directory to the path so we can import valthera_core
sys.path.append(os.path.dirname(__file__))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    get_user_id_from_event
)
from valthera_core import validate_required_fields
from valthera_core import success_response, error_response, validation_error_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Create a new data source for the authenticated user."""
    try:
        log_request_info(event)
        
        # Parse request body
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        
        # Validate required fields
        required_fields = ['name']
        missing_fields = validate_required_fields(data, required_fields)
        if missing_fields:
            return validation_error_response(missing_fields, 'Missing required fields')
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Generate data source ID
        datasource_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Generate user-scoped folder path
        folder_path = f"users/{user_id}/data-sources/{datasource_id}"
        
        # Create data source item for DynamoDB
        datasource_item = {
            'PK': f'USER#{user_id}',
            'SK': f'DATASOURCE#{datasource_id}',
            'GSI1PK': f'DATASOURCE#{datasource_id}',
            'GSI1SK': f'USER#{user_id}',
            'name': data['name'],
            'description': data.get('description', ''),
            'folderPath': folder_path,
            'videoCount': 0,
            'totalSize': 0,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'files': []
        }
        
        # Create S3 folder structure
        try:
            s3_endpoint_url = os.environ.get('S3_ENDPOINT_URL')
            print(f"S3_ENDPOINT_URL: {s3_endpoint_url}")
            print(f"All environment variables: {dict(os.environ)}")
            
            if s3_endpoint_url:
                # For Docker containers, use host.docker.internal to connect to host
                if s3_endpoint_url.startswith('http://localhost:'):
                    s3_endpoint_url = s3_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Using local S3 endpoint: {s3_endpoint_url}")
                s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, region_name='us-east-1')
            else:
                print("Using AWS S3 (no local endpoint)")
                s3_client = boto3.client('s3')
            
            # Determine which bucket to use based on environment
            bucket_name = os.environ.get('DATASOURCES_BUCKET_NAME', Config.VIDEO_BUCKET)
            print(f"Using bucket: {bucket_name}")
            
            # Create the folder by uploading a placeholder object that will be overwritten when files are uploaded
            s3_key = f"{folder_path}/.placeholder"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=b'',  # Empty content
                ContentType='application/octet-stream'
            )
            log_request_info(f"Created S3 folder structure: {folder_path} in bucket {bucket_name}")
        except Exception as s3_error:
            log_error(s3_error, {'function': 'create_s3_folder', 'folder_path': folder_path})
            # Don't fail the request if S3 folder creation fails, it will be created on first upload
        
        # Store in DynamoDB
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        print(f"AWS_ENDPOINT_URL: {aws_endpoint_url}")
        
        if aws_endpoint_url:
            # For Docker containers, use host.docker.internal to connect to host
            if aws_endpoint_url.startswith('http://localhost:'):
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
            dynamodb = boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
        else:
            print("Using AWS DynamoDB (no local endpoint)")
            dynamodb = boto3.resource('dynamodb')
        
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"Table name: {table_name}")
        table = dynamodb.Table(table_name)
        
        table.put_item(Item=datasource_item)
        
        # Return success response
        response_data = {
            'id': datasource_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'folderPath': folder_path,
            'videoCount': 0,
            'totalSize': 0,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'files': []
        }
        
        response = success_response(response_data, 201)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'create_datasource', 'event': event})
        return error_response('Internal server error', 500) 