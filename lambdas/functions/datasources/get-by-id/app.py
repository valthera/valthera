import json
import boto3
import base64
import sys
import os
from decimal import Decimal
from valthera_core import get_user_id_from_event

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_dynamodb_resource():
    """Get DynamoDB resource with proper endpoint configuration."""
    aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    if aws_endpoint_url:
        # For Docker containers, use host.docker.internal to connect to host
        if aws_endpoint_url.startswith('http://localhost:'):
            aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
        
        # For local development, use simple endpoint configuration
        return boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
    else:
        return boto3.resource('dynamodb')

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

def get_cors_headers():
    """Get CORS headers for the response."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,X-Requested-With',
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE,PATCH',
        'Access-Control-Allow-Credentials': 'true'
    }

def success_response(data, status_code=200):
    """Create a successful response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def error_response(message, status_code=400):
    """Create an error response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': message})
    }

def not_found_response(resource_type, resource_id):
    """Create a not found response."""
    return {
        'statusCode': 404,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'error': f'{resource_type} not found: {resource_id}',
            'code': 'NOT_FOUND'
        })
    }

def lambda_handler(event, context):
    """Get a specific data source by ID."""
    try:
        print(f"Event: {json.dumps(event)}")
        
        # Handle OPTIONS request for CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Get data source ID from path parameters
        datasource_id = event.get('pathParameters', {}).get('datasourceId')
        if not datasource_id:
            return error_response('Data source ID is required', 400)
        
        # Get user ID from event
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401)
        
        # Get DynamoDB resource
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
        
        datasource = response['Item']
        
        # Transform to API response format
        response_data = transform_datasource_item(datasource)
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error getting datasource by ID: {e}")
        return error_response('Internal server error', 500)


def transform_datasource_item(item):
    """Transform DynamoDB item to API response format."""
    datasource_id = item['SK'].replace('DATASOURCE#', '')
    
    return {
        'id': datasource_id,
        'name': item.get('name', ''),
        'description': item.get('description', ''),
        'folderPath': item.get('folderPath', ''),
        'videoCount': item.get('videoCount', 0),
        'totalSize': item.get('totalSize', 0),
        'createdAt': item.get('createdAt', ''),
        'updatedAt': item.get('updatedAt', ''),
        'files': item.get('files', [])
    }