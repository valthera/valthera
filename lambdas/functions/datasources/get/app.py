import json
import boto3
import os
from decimal import Decimal

from valthera_core import (
    get_user_id_from_event,
    success_response,
    error_response,
    get_cors_headers,
    get_dynamodb_resource
)

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

## Using shared get_dynamodb_resource from valthera_core which handles
## local Docker vs host endpoint resolution consistently across functions

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
        
        # Debug environment variables
        print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
        print(f"AWS_ENDPOINT_URL: {os.environ.get('AWS_ENDPOINT_URL')}")
        print(f"LOCAL_DEFAULT_USER_ID: {os.environ.get('LOCAL_DEFAULT_USER_ID')}")
        
        if not user_id:
            print("No user ID found in request")
            # For local development, we might want to allow unauthenticated requests
            # but for now, we'll return an error to ensure proper authentication
            return error_response('Unauthorized - No valid user ID found', 401)
        
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
            print(f"Error in lambda_handler: {db_error}")
            import traceback
            traceback.print_exc()
            return error_response('Database connection failed', 500, 'DATABASE_ERROR')
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return error_response('Internal server error', 500) 