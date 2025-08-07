import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """Get a specific project by ID."""
    try:
        # Get user ID from authorizer
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('sub')
        if not user_id:
            return error_response('Unauthorized', 401)
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        # Get project from DynamoDB
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
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
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
        }
        
    except Exception as e:
        print(f"Error getting project: {e}")
        return error_response('Internal server error', 500)

def error_response(message, status_code):
    """Return an error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({'error': message})
    } 