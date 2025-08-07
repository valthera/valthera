import json
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """Update a project."""
    try:
        # Get user ID from authorizer
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('sub')
        if not user_id:
            return error_response('Unauthorized', 401)
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        description = body.get('description')
        has_droid_dataset = body.get('hasDroidDataset')
        linked_data_sources = body.get('linkedDataSources')
        
        # Get existing project
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        project = response.get('Item')
        if not project or project.get('type') != 'project':
            return error_response('Project not found', 404)
        
        # Update fields
        update_expression = "SET updated_at = :updated_at"
        expression_attribute_values = {
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        if name is not None:
            update_expression += ", #n = :name"
            expression_attribute_values[':name'] = name
            expression_attribute_names = {'#n': 'name'}
        
        if description is not None:
            update_expression += ", description = :description"
            expression_attribute_values[':description'] = description
        
        if has_droid_dataset is not None:
            update_expression += ", has_droid_dataset = :has_droid_dataset"
            expression_attribute_values[':has_droid_dataset'] = has_droid_dataset
        
        if linked_data_sources is not None:
            update_expression += ", linked_data_sources = :linked_data_sources"
            expression_attribute_values[':linked_data_sources'] = linked_data_sources
        
        # Update project
        table.update_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if 'name' in locals() else None
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
                'message': 'Project updated successfully'
            })
        }
        
    except Exception as e:
        print(f"Error updating project: {e}")
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