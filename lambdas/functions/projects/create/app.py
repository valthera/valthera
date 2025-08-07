import json
import os
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """Create a new project."""
    try:
        # Get user ID from authorizer
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('sub')
        if not user_id:
            return error_response('Unauthorized', 401)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        description = body.get('description', '')
        has_droid_dataset = body.get('hasDroidDataset', False)
        linked_data_sources = body.get('linkedDataSources', [])
        
        if not name:
            return error_response('Project name is required', 400)
        
        # Generate project ID
        project_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Create project item
        project_item = {
            'PK': f'USER#{user_id}',
            'SK': f'PROJECT#{project_id}',
            'GSI1PK': f'PROJECT#{project_id}',
            'GSI1SK': f'PROJECT#{project_id}',
            'type': 'project',
            'project_id': project_id,
            'name': name,
            'description': description,
            'has_droid_dataset': has_droid_dataset,
            'linked_data_sources': linked_data_sources,
            'created_at': timestamp,
            'updated_at': timestamp,
            'user_id': user_id
        }
        
        # Save to DynamoDB
        table.put_item(Item=project_item)
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'id': project_id,
                'name': name,
                'description': description,
                'hasDroidDataset': has_droid_dataset,
                'linkedDataSources': linked_data_sources,
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'videoCount': 0,
                'status': 'active'
            })
        }
        
    except Exception as e:
        print(f"Error creating project: {e}")
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