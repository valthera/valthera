import json
import boto3
import uuid
import base64
from datetime import datetime
import sys
import os
from decimal import Decimal

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

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present."""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    return missing_fields

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
        dynamodb = get_dynamodb_resource()
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        
        # Save to DynamoDB
        table.put_item(Item=datasource_item)
        
        # Create S3 folder structure (optional for local development)
        try:
            s3_endpoint_url = os.environ.get('S3_ENDPOINT_URL')
            print(f"S3_ENDPOINT_URL: {s3_endpoint_url}")
            
            if s3_endpoint_url:
                # For Docker containers, use host.docker.internal to connect to host
                if s3_endpoint_url.startswith('http://localhost:'):
                    s3_endpoint_url = s3_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Using local S3 endpoint: {s3_endpoint_url}")
                s3_client = boto3.client('s3', 
                                       endpoint_url=s3_endpoint_url, 
                                       region_name='us-east-1',
                                       aws_access_key_id='dummy',
                                       aws_secret_access_key='dummy')
            else:
                print("Using AWS S3 (no local endpoint)")
                s3_client = boto3.client('s3')
            
            # Use a default bucket name for local development
            bucket_name = os.environ.get('DATASOURCES_BUCKET_NAME', 'valthera-dev-datasources')
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