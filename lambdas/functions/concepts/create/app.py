import boto3
import json
import os
import uuid
from datetime import datetime
from decimal import Decimal
import base64
from valthera_core import get_user_id_from_event

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

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



def require_authentication(user_id):
    """Check if authentication is required."""
    return user_id is None

def get_auth_error_response():
    """Get authentication error response."""
    return {
        'statusCode': 401,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': 'User not authenticated'})
    }

def get_cors_headers():
    """Get CORS headers."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
        'Access-Control-Allow-Methods': 'DELETE,GET,OPTIONS,POST,PUT',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Access-Control-Allow-Origin,Access-Control-Allow-Credentials'
    }

def success_response(data, status_code=200):
    """Create a successful response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def error_response(message, status_code=400, code=None):
    """Create an error response."""
    response_data = {
        'error': message,
        'code': code or 'ERROR'
    }
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(response_data, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    """Create a new concept for a project."""
    try:
        print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
        
        # Handle OPTIONS request for CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        print(f"Project ID: {project_id}")
        
        # Get user ID from the event
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        # Check if authentication is required
        if require_authentication(user_id):
            return get_auth_error_response()
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        
        # Validate required fields
        name = body.get('name', '').strip()
        if not name:
            return error_response('Concept name is required', 400)
        
        description = body.get('description', '').strip()
        
        # Generate concept ID
        concept_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        
        # Create concept item
        concept_item = {
            'PK': f'PROJECT#{project_id}',
            'SK': f'CONCEPT#{concept_id}',
            'GSI1PK': f'CONCEPT#{concept_id}',
            'GSI1SK': f'CONCEPT#{concept_id}',
            'type': 'concept',
            'concept_id': concept_id,
            'name': name,
            'description': description,
            'created_at': current_time,
            'updated_at': current_time,
            'status': 'active',
            'sample_count': 0,
            'video_count': 0,
            'linked_videos': []
        }
        
        # Save to DynamoDB
        table.put_item(Item=concept_item)
        
        # Return success response
        return success_response({
            'id': concept_id,
            'name': name,
            'description': description,
            'uploadedAt': current_time,
            'status': 'active',
            'sampleCount': 0,
            'videoCount': 0,
            'linkedVideos': []
        })
        
    except Exception as e:
        print(f"Error creating concept: {e}")
        return error_response('Internal server error', 500) 