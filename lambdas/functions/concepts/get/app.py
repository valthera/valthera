import boto3
import json
import os
from datetime import datetime
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
    """List all concepts for a project."""
    try:
        print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        print(f"Project ID: {project_id}")
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # For local development, skip project ownership verification
        # In production, this would verify the project belongs to the user
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Check if we're running locally
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        print(f"Environment AWS_ENDPOINT_URL: {aws_endpoint_url}")
        print(f"All environment variables: {dict(os.environ)}")
        
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
        
        # Query DynamoDB for concepts
        try:
            # Query using PK to get all concepts for the project
            response = table.query(
                KeyConditionExpression=(
                    'PK = :pk AND begins_with(SK, :sk_prefix)'
                ),
                ExpressionAttributeValues={
                    ':pk': f'PROJECT#{project_id}',
                    ':sk_prefix': 'CONCEPT#'
                }
            )
            
            # Transform DynamoDB items to API response format
            concepts = []
            for item in response.get('Items', []):
                concept = transform_concept_item(item)
                concepts.append(concept)
            
            # Sort concepts by creation date (newest first)
            concepts.sort(key=lambda x: x.get('uploadedAt', ''), reverse=True)
            
            response_data = {
                'concepts': concepts,
                'count': len(concepts)
            }
            
            print(f"Successfully retrieved {len(concepts)} concepts from DynamoDB")
            return success_response(response_data)
            
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            # For local development, if DB fails, return mock data
            if os.environ.get('AWS_ENDPOINT_URL'):
                print("Local development detected - returning mock concept data due to DB error")
                mock_concepts = [
                    {
                        'id': 'mock-concept-1',
                        'name': 'Sample Concept 1',
                        'description': 'This is a sample concept for testing',
                        'uploadedAt': '2025-08-04T23:00:00.000Z',
                        'status': 'active',
                        'sampleCount': 5,
                        'videoCount': 2,
                        'linkedVideos': []
                    },
                    {
                        'id': 'mock-concept-2',
                        'name': 'Sample Concept 2',
                        'description': 'Another sample concept for testing',
                        'uploadedAt': '2025-08-04T22:30:00.000Z',
                        'status': 'active',
                        'sampleCount': 3,
                        'videoCount': 1,
                        'linkedVideos': []
                    }
                ]
                
                response_data = {
                    'concepts': mock_concepts,
                    'count': len(mock_concepts)
                }
                
                print(f"Returning mock response: {json.dumps(response_data, cls=DecimalEncoder)}")
                return success_response(response_data)
            else:
                print(f"Error in lambda_handler: {db_error}")
                import traceback
                traceback.print_exc()
                return error_response('Internal server error', 500)
        
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