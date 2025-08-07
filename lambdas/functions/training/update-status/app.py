import json
import boto3
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info
)
from valthera_core import success_response, error_response, not_found_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Update training job status and progress."""
    try:
        log_request_info(event)
        
        # Get project and training IDs from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        training_id = event.get('pathParameters', {}).get('id')
        
        if not project_id or not training_id:
            return error_response('Project ID and Training ID are required', 400)
        
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
            return not_found_response('Project', project_id)
        
        # Get training job from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        # Check if training job exists
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'TRAINING#{training_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Training job', training_id)
        
        training_job = response['Item']
        
        # Prepare update expression
        update_expression = 'SET updatedAt = :updatedAt'
        expression_attribute_values = {
            ':updatedAt': datetime.utcnow().isoformat()
        }
        
        # Add fields to update
        allowed_fields = ['status', 'progress', 'logs', 'completedAt']
        for field in allowed_fields:
            if field in data:
                update_expression += f', {field} = :{field}'
                expression_attribute_values[f':{field}'] = data[field]
        
        # Validate status transition
        current_status = training_job.get('status', 'preprocessing')
        new_status = data.get('status', current_status)
        
        if not is_valid_status_transition(current_status, new_status):
            return error_response(f'Invalid status transition from {current_status} to {new_status}', 400, 'VALIDATION_ERROR')
        
        # Update training job in DynamoDB
        table.update_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'TRAINING#{training_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # If training completed, update related behaviors
        if new_status == 'completed':
            update_behavior_training_results(table, project_id, training_id, data)
        
        # Get updated training job
        updated_response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'TRAINING#{training_id}'
            }
        )
        
        # Transform and return updated training job
        training_job = transform_training_job_item(updated_response['Item'])
        
        response_data = success_response(training_job)
        log_response_info(response_data)
        return response_data
        
    except Exception as e:
        log_error(e, {'function': 'update_training_status', 'event': event})
        return error_response('Internal server error', 500)


def get_user_id_from_event(event):
    """Extract user ID from Cognito authorizer context."""
    try:
        # Get user ID from Cognito authorizer
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        user_id = authorizer_context.get('sub') or authorizer_context.get('user_id')
        
        if not user_id:
            # Fallback to headers if authorizer not available
            user_id = event.get('headers', {}).get('X-User-ID')
        
        return user_id
    except Exception as e:
        log_error(e, {'function': 'get_user_id_from_event'})
        return None


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


def is_valid_status_transition(current_status, new_status):
    """Validate status transition."""
    valid_transitions = {
        'preprocessing': ['training', 'failed'],
        'training': ['validating', 'failed'],
        'validating': ['completed', 'failed'],
        'completed': [],  # Terminal state
        'failed': []      # Terminal state
    }
    
    return new_status in valid_transitions.get(current_status, [])


def update_behavior_training_results(table, project_id, training_id, data):
    """Update behavior training results when training completes."""
    try:
        # Query for behaviors in the project
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'PROJECT#{project_id}',
                ':sk_prefix': 'BEHAVIOR#'
            }
        )
        
        # Update each behavior with training results
        for behavior in response.get('Items', []):
            training_results = {
                'accuracy': data.get('accuracy'),
                'modelPath': data.get('modelPath'),
                'trainingJobId': training_id,
                'lastTrainedAt': datetime.utcnow().isoformat()
            }
            
            table.update_item(
                Key={
                    'PK': behavior['PK'],
                    'SK': behavior['SK']
                },
                UpdateExpression='SET trainingResults = :trainingResults, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':trainingResults': training_results,
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        log_error(e, {'function': 'update_behavior_training_results', 'project_id': project_id, 'training_id': training_id})
        # Continue even if behavior update fails


def transform_training_job_item(item):
    """Transform DynamoDB item to API response format."""
    training_id = item['SK'].replace('TRAINING#', '')
    project_id = item['PK'].replace('PROJECT#', '')
    
    return {
        'id': training_id,
        'projectId': project_id,
        'status': item.get('status', 'preprocessing'),
        'progress': item.get('progress', 0),
        'startedAt': item.get('startedAt', ''),
        'completedAt': item.get('completedAt'),
        'logs': item.get('logs', []),
        'config': item.get('config', {})
    } 