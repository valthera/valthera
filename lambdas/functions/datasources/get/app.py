import json
import boto3
import os
import sys
from decimal import Decimal
import base64

# Add the current directory to the path so we can import valthera_core
sys.path.append(os.path.dirname(__file__))

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

def transform_datasource_item(item):
    """Transform DynamoDB item to API response format."""
    datasource_id = item.get('SK', '').replace('DATASOURCE#', '')
    
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

def lambda_handler(event, context):
    """List all data sources for the authenticated user."""
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
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"Table name: {table_name}")
        table = dynamodb.Table(table_name)
        
        # Query using PK to get all datasources for the user
        try:
            response = table.query(
                KeyConditionExpression=(
                    'PK = :pk AND begins_with(SK, :sk_prefix)'
                ),
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk_prefix': 'DATASOURCE#'
                }
            )
            
            # Transform DynamoDB items to API response format
            datasources = []
            for item in response.get('Items', []):
                datasource = transform_datasource_item(item)
                datasources.append(datasource)
            
            # Sort datasources by creation date (newest first)
            datasources.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
            
            response_data = {
                'datasources': datasources,
                'count': len(datasources)
            }
            
            print(f"Successfully retrieved {len(datasources)} datasources from DynamoDB")
            return success_response(response_data)
            
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            # For local development, if DB fails, return mock data
            if os.environ.get('AWS_ENDPOINT_URL'):
                print("Local development detected - returning mock datasource data due to DB error")
                mock_datasources = [
                    {
                        'id': 'mock-datasource-1',
                        'name': 'Sample Data Source 1',
                        'description': 'This is a sample data source for testing',
                        'folderPath': '/sample/folder1',
                        'videoCount': 5,
                        'totalSize': 1024000,
                        'createdAt': '2025-08-04T23:00:00.000Z',
                        'updatedAt': '2025-08-04T23:00:00.000Z',
                        'files': []
                    },
                    {
                        'id': 'mock-datasource-2',
                        'name': 'Sample Data Source 2',
                        'description': 'Another sample data source for testing',
                        'folderPath': '/sample/folder2',
                        'videoCount': 3,
                        'totalSize': 512000,
                        'createdAt': '2025-08-04T22:30:00.000Z',
                        'updatedAt': '2025-08-04T22:30:00.000Z',
                        'files': []
                    }
                ]
                
                response_data = {
                    'datasources': mock_datasources,
                    'count': len(mock_datasources)
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