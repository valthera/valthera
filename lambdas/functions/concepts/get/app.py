import boto3
import json
import os
from datetime import datetime
from decimal import Decimal

from valthera_core import (
    get_user_id_from_event,
    success_response,
    error_response,
    get_cors_headers,
    not_found_response
)

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
            print(f"Error in lambda_handler: {db_error}")
            import traceback
            traceback.print_exc()
            return error_response('Database connection failed', 500, 'DATABASE_ERROR')
        
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