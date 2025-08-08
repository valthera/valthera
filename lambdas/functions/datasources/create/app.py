import json
import boto3
import uuid
import base64
from datetime import datetime
import sys
import os
from decimal import Decimal
from valthera_core import (
    get_user_id_from_event,
    success_response,
    error_response,
    get_cors_headers,
    get_dynamodb_resource,
    get_s3_client,
    Config
)

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

## Use shared get_dynamodb_resource from valthera_core

def decode_jwt_payload(token):
    """Decode JWT payload without verification (for local development)."""
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present."""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    return missing_fields

## Use shared response helpers from valthera_core

def validation_error_response(missing_fields, message):
    """Create a validation error response."""
    return {
        'statusCode': 400,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'error': message,
            'missing_fields': missing_fields
        })
    }

def lambda_handler(event, context):
    """Create a new data source for the authenticated user."""
    try:
        print(f"Event: {json.dumps(event)}")
        
        # Handle OPTIONS request for CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
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
        
        # Get user ID from event
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401)
        
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
        
        # Get DynamoDB resource and save to DynamoDB
        print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
        print(f"AWS_ENDPOINT_URL: {os.environ.get('AWS_ENDPOINT_URL')}")
        dynamodb = get_dynamodb_resource()
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"Table name: {table_name}")
        table = dynamodb.Table(table_name)
        
        # Save to DynamoDB
        table.put_item(Item=datasource_item)
        
        # Create S3 folder structure (optional for local development)
        try:
            # Use shared S3 client helper which handles local endpoint mapping
            s3_client = get_s3_client()
            
            # Use a default bucket name for local development
            bucket_name = os.environ.get('DATASOURCES_BUCKET_NAME', 'valthera-dev-datasources')
            # If running against local S3, use the local bucket created by valthera-local
            if Config.S3_ENDPOINT_URL:
                bucket_name = 'valthera-datasources'
            print(f"Using bucket: {bucket_name}")
            
            # Create the folder by uploading a placeholder object
            s3_key = f"{folder_path}/.placeholder"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=b'',  # Empty content
                ContentType='application/octet-stream'
            )
            
            print(f"Successfully created S3 folder: {folder_path}")
            
        except Exception as s3_error:
            print(f"S3 error (non-critical for local development): {s3_error}")
            # For local development, S3 errors are not critical
            pass
        
        # Return success response
        return success_response({
            'id': datasource_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'folderPath': folder_path,
            'videoCount': 0,
            'totalSize': 0,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'files': []
        }, 201)
        
    except Exception as e:
        print(f"Error creating datasource: {e}")
        return error_response('Internal server error', 500) 