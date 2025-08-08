import json
import os
import boto3
from decimal import Decimal
from valthera_core import (
    get_user_id_from_event,
    get_dynamodb_resource,
    success_response,
    error_response,
    get_cors_headers,
    DecimalEncoder
)

def lambda_handler(event, context):
    """Get all projects for a user."""
    try:
        print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
        
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
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        
        # Query projects for the user
        try:
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'PROJECT#'
                }
            )
            
            # Format projects
            projects = []
            for item in response.get('Items', []):
                if item.get('type') == 'project':
                    projects.append({
                        'id': item.get('project_id'),
                        'name': item.get('name'),
                        'description': item.get('description', ''),
                        'hasDroidDataset': item.get('has_droid_dataset', False),
                        'linkedDataSources': item.get('linked_data_sources', []),
                        'createdAt': item.get('created_at'),
                        'updatedAt': item.get('updated_at'),
                        'videoCount': 0,  # Default value for now
                        'status': 'active'  # Default status
                    })
            
            # Return success response - return projects array directly
            print(f"Returning {len(projects)} projects")
            return success_response(projects)
            
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            print(f"AWS_ENDPOINT_URL: {os.environ.get('AWS_ENDPOINT_URL')}")
            print(f"All environment variables: {dict(os.environ)}")
            return error_response('Database connection failed', 500, 'DATABASE_ERROR')
                
    except Exception as e:
        print(f"Unexpected error: {e}")
        return error_response('Internal server error', 500, 'INTERNAL_ERROR') 