import json
import os
import boto3
from botocore.exceptions import ClientError
import base64

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
        'body': json.dumps(data)
    }

def error_response(message, status_code=400):
    """Return an error response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': message})
    }

# Initialize table name
table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')

def lambda_handler(event, context):
    """Get a specific project by ID."""
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
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        # Get DynamoDB resource and get project from DynamoDB
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        project = response.get('Item')
        if not project or project.get('type') != 'project':
            return error_response('Project not found', 404)
        
        # Return project
        return success_response({
            'id': project.get('project_id'),
            'name': project.get('name'),
            'description': project.get('description', ''),
            'hasDroidDataset': project.get('has_droid_dataset', False),
            'linkedDataSources': project.get('linked_data_sources', []),
            'createdAt': project.get('created_at'),
            'updatedAt': project.get('updated_at'),
            'videoCount': 0,
            'status': 'active'
        })
        
    except Exception as e:
        print(f"Error getting project: {e}")
        return error_response('Internal server error', 500) 