import boto3
import json
import os
import uuid
from datetime import datetime
from decimal import Decimal
from valthera_core.auth import (
    get_user_id_from_event, 
    require_authentication, 
    get_auth_error_response
)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

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
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Check if we're running locally
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        if aws_endpoint_url:
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
            # Replace localhost with host.docker.internal for Docker container access
            if aws_endpoint_url.startswith('http://localhost:'):
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Updated endpoint URL: {aws_endpoint_url}")
            
            dynamodb = boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
        
        # Use the main table
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"MAIN_TABLE_NAME env var: {os.environ.get('MAIN_TABLE_NAME')}")
        print(f"Using table: {table_name}")
        table = dynamodb.Table(table_name)
        
        # Create concept item for DynamoDB
        concept_item = {
            'PK': f'PROJECT#{project_id}',
            'SK': f'CONCEPT#{concept_id}',
            'name': name,
            'description': description,
            'uploadedAt': current_time,
            'status': 'active',
            'sampleCount': 0,
            'videoCount': 0,
            'linkedVideos': []
        }
        
        # Try to save to DynamoDB
        try:
            # Save to DynamoDB
            table.put_item(Item=concept_item)
            print(f"Successfully saved concept to DynamoDB: {concept_id}")
            
            # Transform to API response format
            response_data = {
                'id': concept_id,
                'name': name,
                'description': description,
                'uploadedAt': current_time,
                'status': 'active',
                'sampleCount': 0,
                'videoCount': 0,
                'linkedVideos': []
            }
            
            return success_response(response_data, 201)
            
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            print(f"Error type: {type(db_error)}")
            
            # For local development, if it's a connection error, return mock data
            if os.environ.get('AWS_ENDPOINT_URL') and 'Connection' in str(db_error):
                print("Local development detected - returning mock concept data due to connection error")
                mock_concept_id = f'mock-concept-{concept_id}'
                
                response_data = {
                    'id': mock_concept_id,
                    'name': name,
                    'description': description,
                    'uploadedAt': current_time,
                    'status': 'active',
                    'sampleCount': 0,
                    'videoCount': 0,
                    'linkedVideos': []
                }
                
                print(f"Returning mock response: {json.dumps(response_data, cls=DecimalEncoder)}")
                return success_response(response_data, 201)
            else:
                import traceback
                traceback.print_exc()
                return error_response(f'Database error: {str(db_error)}', 500)
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return error_response('Internal server error', 500) 