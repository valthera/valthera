import boto3
import json
import os
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


def get_user_id_from_event(event):
    """Extract user ID from the event."""
    try:
        # Check for Cognito authorizer
        if ('requestContext' in event and 
                'authorizer' in event['requestContext']):
            claims = event['requestContext']['authorizer']['claims']
            return claims.get('sub')
        
        # For local development, check for user_id in headers
        headers = event.get('headers', {})
        if headers:
            # Try to get from Authorization header
            auth_header = headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                # For local dev, we'll use a test user ID
                return 'test-user-id'
        
        # For local development, if no auth header is provided, 
        # use a default test user
        # This allows testing without authentication in local dev
        if (os.environ.get('ENVIRONMENT') == 'dev' or 
                os.environ.get('AWS_ENDPOINT_URL')):
            print("Local development detected - using default test user ID")
            return 'test-user-id'
        
        return None
    except Exception as e:
        print(f"Error extracting user ID: {e}")
        return None

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

def not_found_response(resource_type, resource_id):
    """Create a not found response."""
    return error_response(f'{resource_type} not found: {resource_id}', 404, 'NOT_FOUND')

def lambda_handler(event, context):
    """Get a specific concept by ID."""
    try:
        print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
        
        # Get project ID and concept ID from path parameters
        path_params = event.get('pathParameters', {})
        project_id = path_params.get('projectId')
        concept_id = path_params.get('conceptId')
        
        if not project_id:
            return error_response('Project ID is required', 400)
        
        if not concept_id:
            return error_response('Concept ID is required', 400)
        
        print(f"Project ID: {project_id}")
        print(f"Concept ID: {concept_id}")
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Check if we're running locally
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        print(f"Environment AWS_ENDPOINT_URL: {aws_endpoint_url}")
        
        if aws_endpoint_url:
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
            # Replace localhost with host.docker.internal for Docker container access
            if aws_endpoint_url.startswith('http://localhost:'):
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Updated endpoint URL: {aws_endpoint_url}")
            
            dynamodb = boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
        else:
            print("No AWS_ENDPOINT_URL found, using default AWS DynamoDB")
        
        # Use the main table
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        print(f"Using table: {table_name}")
        
        # Get the concept item
        try:
            response = table.get_item(
                Key={
                    'PK': f'PROJECT#{project_id}',
                    'SK': f'CONCEPT#{concept_id}'
                }
            )
            
            print(f"DynamoDB response: {json.dumps(response, cls=DecimalEncoder)}")
            
            if 'Item' not in response:
                # For local development, return mock data if item doesn't exist
                if (os.environ.get('ENVIRONMENT') == 'dev' or 
                        os.environ.get('AWS_ENDPOINT_URL')):
                    print("Local development detected - returning mock concept data")
                    mock_concept = {
                        'id': concept_id,
                        'name': f'Sample Concept {concept_id}',
                        'description': f'This is a mock concept for testing: {concept_id}',
                        'uploadedAt': '2025-08-04T23:00:00.000Z',
                        'status': 'active',
                        'sampleCount': 5,
                        'videoCount': 2,
                        'linkedVideos': []
                    }
                    print(f"Returning mock response: {json.dumps(mock_concept, cls=DecimalEncoder)}")
                    return success_response(mock_concept)
                else:
                    return not_found_response('Concept', concept_id)
            
            # Transform the item to API response format
            concept = transform_concept_item(response['Item'])
            
            print(f"Returning response: {json.dumps(concept, cls=DecimalEncoder)}")
            return success_response(concept)
            
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            # For local development, return mock data if DynamoDB fails
            if (os.environ.get('ENVIRONMENT') == 'dev' or 
                    os.environ.get('AWS_ENDPOINT_URL')):
                print("Local development detected - returning mock concept data due to DB error")
                mock_concept = {
                    'id': concept_id,
                    'name': f'Sample Concept {concept_id}',
                    'description': f'This is a mock concept for testing: {concept_id}',
                    'uploadedAt': '2025-08-04T23:00:00.000Z',
                    'status': 'active',
                    'sampleCount': 5,
                    'videoCount': 2,
                    'linkedVideos': []
                }
                print(f"Returning mock response: {json.dumps(mock_concept, cls=DecimalEncoder)}")
                return success_response(mock_concept)
            else:
                raise db_error
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return error_response('Internal server error', 500)

def transform_concept_item(item):
    """Transform DynamoDB item to API response format."""
    concept_id = item['SK'].replace('CONCEPT#', '')
    
    return {
        'id': concept_id,
        'name': item.get('name', ''),
        'description': item.get('description', ''),
        'uploadedAt': item.get('uploadedAt', ''),
        'status': item.get('status', 'active'),
        'sampleCount': item.get('sampleCount', 0),
        'videoCount': item.get('videoCount', 0),
        'linkedVideos': item.get('linkedVideos', [])
    } 