import json
import os
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import base64
from valthera_core import get_user_id_from_event

def get_dynamodb_resource():
    """Get DynamoDB resource with proper endpoint configuration."""
    aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    if aws_endpoint_url:
        # For Docker containers, use host.docker.internal to connect to host
        if aws_endpoint_url.startswith('http://localhost:'):
            aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
        
        # For local development, use dummy credentials and disable SSL verification
        return boto3.resource('dynamodb', 
                            endpoint_url=aws_endpoint_url,
                            aws_access_key_id='dummy',
                            aws_secret_access_key='dummy',
                            region_name='us-east-1',
                            verify=False)
    else:
        return boto3.resource('dynamodb')

# Initialize DynamoDB client
table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')



def get_cors_headers():
    """Get CORS headers."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
        'Access-Control-Allow-Methods': 'DELETE,GET,OPTIONS,POST,PUT',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Access-Control-Allow-Origin,Access-Control-Allow-Credentials'
    }

def success_response(data, status_code=201):
    """Create a successful response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(data)
    }

def error_response(message, status_code=400):
    """Return an error response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': message})
    }

def lambda_handler(event, context):
    """Create a new project."""
    try:
        print(f"Event: {json.dumps(event)}")
        
        # Handle OPTIONS request for CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Get user ID from event
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        if not user_id:
            return error_response('User not authenticated', 401)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        description = body.get('description', '')
        has_droid_dataset = body.get('hasDroidDataset', False)
        linked_data_sources = body.get('linkedDataSources', [])
        
        if not name:
            return error_response('Project name is required', 400)
        
        # Generate project ID
        project_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Create project item
        project_item = {
            'PK': f'USER#{user_id}',
            'SK': f'PROJECT#{project_id}',
            'GSI1PK': f'PROJECT#{project_id}',
            'GSI1SK': f'PROJECT#{project_id}',
            'type': 'project',
            'project_id': project_id,
            'name': name,
            'description': description,
            'has_droid_dataset': has_droid_dataset,
            'linked_data_sources': linked_data_sources,
            'created_at': timestamp,
            'updated_at': timestamp,
            'user_id': user_id
        }
        
        # Get DynamoDB resource and save to DynamoDB
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        table.put_item(Item=project_item)
        
        # Return success response
        return success_response({
            'id': project_id,
            'name': name,
            'description': description,
            'hasDroidDataset': has_droid_dataset,
            'linkedDataSources': linked_data_sources,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'videoCount': 0,
            'status': 'active'
        })
        
    except Exception as e:
        print(f"Error creating project: {e}")
        return error_response('Internal server error', 500) 