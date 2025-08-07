import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """Delete a project."""
    try:
        # Get user ID from authorizer
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('sub')
        if not user_id:
            return error_response('Unauthorized', 401)
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        # Check if project exists
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        project = response.get('Item')
        if not project or project.get('type') != 'project':
            return error_response('Project not found', 404)
        
        # Delete project
        table.delete_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'message': 'Project deleted successfully'
            })
        }
        
    except Exception as e:
        print(f"Error deleting project: {e}")
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