import json
import boto3
import base64
import sys
import os

# Add the current directory to the path so we can import valthera_core
sys.path.append(os.path.dirname(__file__))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    get_user_id_from_event
)
from valthera_core import success_response, error_response, not_found_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Get a specific data source by ID."""
    try:
        log_request_info(event)
        
        # Get data source ID from path parameters
        datasource_id = event.get('pathParameters', {}).get('datasourceId')
        if not datasource_id:
            return error_response('Data source ID is required', 400)
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401)
        
        # Get data source from DynamoDB
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        print(f"AWS_ENDPOINT_URL: {aws_endpoint_url}")
        
        if aws_endpoint_url:
            # For Docker containers, use host.docker.internal to connect to host
            if aws_endpoint_url.startswith('http://localhost:'):
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
            dynamodb = boto3.resource('dynamodb', endpoint_url=aws_endpoint_url)
        else:
            dynamodb = boto3.resource('dynamodb')
        
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        print(f"Table name: {table_name}")
        table = dynamodb.Table(table_name)
        
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Data source', datasource_id)
        
        datasource = response['Item']
        
        # Transform to API response format
        response_data = transform_datasource_item(datasource)
        
        response = success_response(response_data)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'get_datasource_by_id', 'event': event})
        return error_response('Internal server error', 500)


def transform_datasource_item(item):
    """Transform DynamoDB item to API response format."""
    datasource_id = item['SK'].replace('DATASOURCE#', '')
    
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