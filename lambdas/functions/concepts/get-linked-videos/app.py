#!/usr/bin/env python3

import json
import os
import boto3
from decimal import Decimal
from datetime import datetime

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def get_user_id_from_event(event):
    """Extract user ID from Cognito authorizer context."""
    try:
        # For local development, use the actual user ID
        if os.environ.get('AWS_SAM_LOCAL'):
            return 'f1aa1da0-ab4e-4eda-be6e-ce1d452196e3'
        
        # Extract from Cognito authorizer
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        user_id = authorizer_context.get('claims', {}).get('cognito:username')
        return user_id
    except Exception as e:
        print(f"Error extracting user ID: {e}")
        return None

def get_cors_headers():
    """Get CORS headers for local development."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def success_response(data, status_code=200):
    """Return a successful response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            **get_cors_headers()
        },
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def error_response(message, status_code=500, error_code='ERROR'):
    """Return an error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            **get_cors_headers()
        },
        'body': json.dumps({
            'error': message,
            'code': error_code
        })
    }

def not_found_response(resource_type, resource_id):
    """Return a not found response."""
    return error_response(
        f'{resource_type} with ID {resource_id} not found',
        404,
        'NOT_FOUND'
    )

def format_file_size(bytes_size):
    """Format file size in human readable format."""
    if bytes_size == 0:
        return "0 B"
    
    # Convert Decimal to float if needed
    if isinstance(bytes_size, Decimal):
        bytes_size = float(bytes_size)
    elif isinstance(bytes_size, dict) and 'N' in bytes_size:
        bytes_size = float(bytes_size['N'])
    else:
        bytes_size = float(bytes_size)
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_size >= 1024 and i < len(size_names) - 1:
        bytes_size /= 1024.0
        i += 1
    return f"{bytes_size:.1f} {size_names[i]}"

def verify_project_ownership(user_id, project_id):
    """Verify that the user owns the project."""
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')

        # Check if we're running locally
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        if aws_endpoint_url:
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
            # Check if we're running in SAM local (Docker container)
            is_sam_local = os.environ.get('AWS_SAM_LOCAL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
            print(f"Is SAM local: {is_sam_local}")

            # Only replace localhost with host.docker.internal if we're running in Docker
            if aws_endpoint_url.startswith('http://localhost:') and is_sam_local:
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Updated endpoint URL: {aws_endpoint_url}")

            # For local development, use dummy credentials
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=aws_endpoint_url,
                aws_access_key_id='local',
                aws_secret_access_key='local',
                region_name='us-east-1'
            )
        else:
            print("No AWS_ENDPOINT_URL found - using default AWS DynamoDB")

        # Use the main table
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        print(f"Using table: {table_name}")

        # Check if project exists and user has access
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        return 'Item' in response
    except Exception as e:
        print(f"Error verifying project ownership: {e}")
        return False

def lambda_handler(event, context):
    """Get linked videos for a concept."""
    try:
        print(f"Event: {json.dumps(event)}")
        
        # Get project and concept IDs from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        concept_id = event.get('pathParameters', {}).get('conceptId')
        
        print(f"Project ID: {project_id}")
        print(f"Concept ID: {concept_id}")
        
        if not project_id or not concept_id:
            return error_response(
                'Project ID and Concept ID are required', 400
            )
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Verify project ownership - skip for local development
        # Check if we're running locally by looking for local endpoints
        is_local = os.environ.get('AWS_ENDPOINT_URL') or os.environ.get('AWS_SAM_LOCAL')
        if not is_local:  # Only verify ownership in production
            if not verify_project_ownership(user_id, project_id):
                return error_response(
                    'Project not found or access denied', 404, 'NOT_FOUND'
                )
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')

        # Check if we're running locally
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        if aws_endpoint_url:
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
            # Check if we're running in SAM local (Docker container)
            is_sam_local = os.environ.get('AWS_SAM_LOCAL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
            print(f"Is SAM local: {is_sam_local}")

            # Only replace localhost with host.docker.internal if we're running in Docker
            if aws_endpoint_url.startswith('http://localhost:') and is_sam_local:
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Updated endpoint URL: {aws_endpoint_url}")

            # For local development, use dummy credentials
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=aws_endpoint_url,
                aws_access_key_id='local',
                aws_secret_access_key='local',
                region_name='us-east-1'
            )
        else:
            print("No AWS_ENDPOINT_URL found - using default AWS DynamoDB")

        # Use the main table
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        print(f"Using table: {table_name}")
        
        # Check if concept exists
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{concept_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Concept', concept_id)
        
        concept_item = response['Item']
        linked_video_ids = concept_item.get('linkedVideos', [])
        print(f"Linked video IDs: {linked_video_ids}")
        
        # Get all data sources to find video metadata
        # Use scan instead of query to search across all users
        data_sources_response = table.scan(
            FilterExpression='begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':sk_prefix': 'DATASOURCE#'
            }
        )
        
        linked_videos = []
        
        # For each linked video ID, find the corresponding video in data sources
        for video_id in linked_video_ids:
            for data_source_item in data_sources_response.get('Items', []):
                data_source_files = data_source_item.get('files', [])
                print(f"Processing data source: {data_source_item.get('name', 'Unknown')}")
                print(f"Files count: {len(data_source_files)}")
                
                for file in data_source_files:
                    print(f"Checking file: {file}")
                    
                    # Handle both raw DynamoDB format and deserialized format
                    file_s3_key = file.get('s3Key')
                    if isinstance(file_s3_key, dict) and 'S' in file_s3_key:
                        file_s3_key = file_s3_key['S']
                    
                    print(f"File s3Key: {file_s3_key}, Looking for: {video_id}")
                    
                    if file_s3_key == video_id:
                        print(f"Found matching file: {file_s3_key}")
                        
                        # Handle file data extraction with proper type conversion
                        file_size = file.get('fileSize', 0)
                        if isinstance(file_size, dict) and 'N' in file_size:
                            file_size = float(file_size['N'])
                        elif hasattr(file_size, 'as_tuple'):
                            file_size = float(file_size)
                        else:
                            file_size = float(file_size)
                        
                        file_name = file.get('fileName')
                        if isinstance(file_name, dict) and 'S' in file_name:
                            file_name = file_name['S']
                        
                        upload_date = file.get('uploadDate')
                        if isinstance(upload_date, dict) and 'S' in upload_date:
                            upload_date = upload_date['S']
                        
                        processing_status = file.get('processingStatus', 'completed')
                        if isinstance(processing_status, dict) and 'S' in processing_status:
                            processing_status = processing_status['S']
                        
                        metadata = file.get('metadata', {})
                        if isinstance(metadata, dict) and 'M' in metadata:
                            metadata = metadata['M']
                        
                        source_name = data_source_item.get('name', '')
                        if isinstance(source_name, dict) and 'S' in source_name:
                            source_name = source_name['S']
                        
                        linked_videos.append({
                            'id': file_s3_key,
                            'fileName': file_name,
                            'fileSize': int(file_size),  # Keep as int for API consistency
                            'uploadDate': upload_date,
                            's3Key': file_s3_key,
                            'processingStatus': processing_status,
                            'metadata': metadata,
                            'source': source_name,
                            'size': format_file_size(file_size)
                        })
                        break
        
        print(f"Found {len(linked_videos)} linked videos")
        
        # For debugging, let's return the raw data to see what we're getting
        return success_response({
            'linkedVideos': linked_videos,
            'conceptId': concept_id,
            'totalCount': len(linked_videos),
            'debug': {
                'linked_video_ids': linked_video_ids,
                'data_sources_count': len(data_sources_response.get('Items', [])),
                'first_data_source': data_sources_response.get('Items', [])[0] if data_sources_response.get('Items') else None
            }
        })
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return error_response('Internal server error', 500) 