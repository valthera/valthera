import json
import boto3
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info
)
from valthera_core import success_response, error_response, not_found_response
from valthera_core import validate_behavior_name
from valthera_core import get_user_id_from_event
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Update a behavior within a project."""
    try:
        log_request_info(event)
        
        # Get project and behavior IDs from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        behavior_id = event.get('pathParameters', {}).get('id')
        
        if not project_id or not behavior_id:
            return error_response(
                'Project ID and Behavior ID are required', 400
            )
        
        # Parse request body
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Verify project ownership
        if not verify_project_ownership(user_id, project_id):
            return error_response(
                'Project not found or access denied', 404, 'NOT_FOUND'
            )
        
        # Get behavior from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        # Check if behavior exists
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Behavior', behavior_id)
        
        # Validate and prepare update data
        update_data = {}
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Handle name update
        if 'name' in data:
            is_valid, error_message = validate_behavior_name(data['name'])
            if not is_valid:
                return error_response(error_message, 400, 'VALIDATION_ERROR')
            
            update_data['name'] = data['name']
            update_expression_parts.append('#name = :name')
            expression_attribute_values[':name'] = data['name']
            expression_attribute_names['#name'] = 'name'
        
        # Handle description update
        if 'description' in data:
            update_data['description'] = data['description']
            update_expression_parts.append('#description = :description')
            expression_attribute_values[':description'] = data['description']
            expression_attribute_names['#description'] = 'description'
        
        # Always update the updatedAt timestamp
        update_expression_parts.append('#updatedAt = :updatedAt')
        expression_attribute_values[':updatedAt'] = datetime.utcnow().isoformat()
        expression_attribute_names['#updatedAt'] = 'updatedAt'
        
        if not update_expression_parts:
            return error_response('No valid fields to update', 400, 'VALIDATION_ERROR')
        
        # Update the behavior in DynamoDB
        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        table.update_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues='ALL_NEW'
        )
        
        # Get the updated behavior
        updated_response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            }
        )
        
        updated_behavior = updated_response['Item']
        
        # Transform to API response format
        response_data = transform_behavior_item(updated_behavior)
        
        response = success_response(response_data)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'update_behavior', 'event': event})
        return error_response('Internal server error', 500)





def verify_project_ownership(user_id, project_id):
    """Verify that the project exists and belongs to the user."""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        return 'Item' in response
    except Exception as e:
        log_error(e, {'function': 'verify_project_ownership', 'user_id': user_id, 'project_id': project_id})
        return False


def transform_behavior_item(item):
    """Transform DynamoDB item to API response format."""
    behavior_id = item['SK'].replace('CONCEPT#', '')
    project_id = item['PK'].replace('PROJECT#', '')
    
    return {
        'id': behavior_id,
        'projectId': project_id,
        'name': item.get('name', ''),
        'description': item.get('description', ''),
        'sampleCount': item.get('sampleCount', 0),
        'uploadedAt': item.get('uploadedAt', ''),
        'updatedAt': item.get('updatedAt', ''),
        'linkedVideos': item.get('linkedVideos', []),
        'trainingResults': item.get('trainingResults', {}),
        'apiEndpoints': item.get('apiEndpoints', [])
    } 