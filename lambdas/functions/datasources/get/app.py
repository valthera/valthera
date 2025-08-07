import json
import boto3
import os
import sys
from decimal import Decimal

# Add the current directory to the path so we can import valthera_core
sys.path.append(os.path.dirname(__file__))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    get_user_id_from_event
)
from valthera_core import success_response, error_response

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_cors_headers():
    """Get CORS headers for the response."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,X-Requested-With',
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE,PATCH',
        'Access-Control-Allow-Credentials': 'true'
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

@log_execution_time
def lambda_handler(event, context):
    """List all data sources for the authenticated user."""
    try:
        log_request_info(event)
        
        # Handle OPTIONS request for CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        if not user_id:
            return error_response('User not authenticated', 401)
        
        # Query DynamoDB for user's datasources
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        print(f"AWS_ENDPOINT_URL: {aws_endpoint_url}")
        
        if aws_endpoint_url:
            # For Docker containers, use host.docker.internal to connect to host
            if aws_endpoint_url.startswith('http://localhost:'):
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
            dynamodb = boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
        else:
            dynamodb = boto3.resource('dynamodb')
            print("Using AWS DynamoDB (no local endpoint)")
        
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
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            return error_response('Failed to retrieve data sources', 500)
        
        # Transform DynamoDB items to API response format
        datasources = []
        for item in response.get('Items', []):
            datasource = transform_datasource_item(item)
            datasources.append(datasource)
        
        # Sort data sources by creation date (newest first)
        datasources.sort(key=lambda x: x['createdAt'], reverse=True)
        
        response = success_response(datasources)
        print(f"Response: {json.dumps(response)}")
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        return error_response('Internal server error', 500) 