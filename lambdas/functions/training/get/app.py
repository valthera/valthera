import boto3
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
    """List all training jobs for a project."""
    try:
        log_request_info(event)
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Verify project ownership
        if not verify_project_ownership(user_id, project_id):
            return not_found_response('Project', project_id)
        
        # Query DynamoDB for project's training jobs
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        # Query using PK to get all training jobs for the project
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'PROJECT#{project_id}',
                ':sk_prefix': 'TRAINING#'
            }
        )
        
        # Transform DynamoDB items to API response format
        training_jobs = []
        for item in response.get('Items', []):
            training_job = transform_training_job_item(item)
            training_jobs.append(training_job)
        
        # Sort training jobs by creation date (newest first)
        training_jobs.sort(key=lambda x: x['startedAt'], reverse=True)
        
        response_data = {
            'trainingJobs': training_jobs,
            'count': len(training_jobs)
        }
        
        response = success_response(response_data)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'list_training_jobs', 'event': event})
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