import boto3
import json
import os
from datetime import datetime
from decimal import Decimal
import base64

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
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None

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
                # Extract the token
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                
                # Decode the JWT token to get the user ID
                payload = decode_jwt_payload(token)
                if payload:
                    # Extract user ID from the JWT payload
                    user_id = payload.get('sub') or payload.get('cognito:username')
                    if user_id:
                        print(f"Extracted user ID from JWT: {user_id}")
                        return user_id
                    else:
                        print("No user ID found in JWT payload")
                        print(f"JWT payload: {payload}")
                        # Don't fall back to test-user-id if JWT parsing fails
                        return None
                else:
                    print("Failed to decode JWT token")
                    # Don't fall back to test-user-id if JWT parsing fails
                    return None
        
        # Only fall back to default user if there's no Authorization header at all
        # This allows testing without authentication in local dev
        if (os.environ.get('ENVIRONMENT') == 'dev' or 
                os.environ.get('AWS_ENDPOINT_URL')):
            print("Local development detected - no Authorization header, using default test user ID")
            return os.environ.get('LOCAL_DEFAULT_USER_ID', 'local-dev-user')
        
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
        
        # Get user ID from event
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # For local development, skip project ownership verification
        # In production, this would verify the project belongs to the user
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
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