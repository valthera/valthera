import json
import boto3
import uuid
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    get_user_id_from_event
)
from valthera_core import validate_required_fields
from valthera_core import success_response, error_response, validation_error_response, not_found_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Create a new API endpoint for a behavior after training."""
    try:
        log_request_info(event)
        
        # Get project ID from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        if not project_id:
            return error_response('Project ID is required', 400)
        
        # Parse request body
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        
        # Validate required fields
        required_fields = ['behaviorId', 'classifierName', 'accuracy', 'url']
        missing_fields = validate_required_fields(data, required_fields)
        if missing_fields:
            return validation_error_response(missing_fields, 'Missing required fields')
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Verify project ownership
        if not verify_project_ownership(user_id, project_id):
            return not_found_response('Project', project_id)
        
        # Verify behavior exists and belongs to project
        if not verify_behavior_exists(project_id, data['behaviorId']):
            return not_found_response('Behavior', data['behaviorId'])
        
        # Generate endpoint ID
        endpoint_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Create endpoint item for DynamoDB
        endpoint_item = {
            'PK': f'PROJECT#{project_id}',
            'SK': f'ENDPOINT#{endpoint_id}',
            'behaviorId': data['behaviorId'],
            'classifierName': data['classifierName'],
            'accuracy': data['accuracy'],
            'url': data['url'],
            'status': data.get('status', 'ready'),
            'createdAt': timestamp,
            'usageMetrics': {
                'totalCalls': 0,
                'lastUsed': None,
                'errorRate': 0
            }
        }
        
        # Store in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        table.put_item(Item=endpoint_item)
        
        # Update behavior with endpoint reference
        update_behavior_endpoint(table, project_id, data['behaviorId'], endpoint_id)
        
        # Update project's endpoint count
        update_project_endpoint_count(table, user_id, project_id)
        
        # Return success response
        response_data = {
            'id': endpoint_id,
            'projectId': project_id,
            'behaviorId': data['behaviorId'],
            'classifierName': data['classifierName'],
            'accuracy': data['accuracy'],
            'url': data['url'],
            'status': data.get('status', 'ready'),
            'createdAt': timestamp,
            'usageMetrics': {
                'totalCalls': 0,
                'lastUsed': None,
                'errorRate': 0
            }
        }
        
        response = success_response(response_data, 201)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'create_endpoint', 'event': event})
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


def verify_behavior_exists(project_id, behavior_id):
    """Verify that the behavior exists and belongs to the project."""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'BEHAVIOR#{behavior_id}'
            }
        )
        
        return 'Item' in response
    except Exception as e:
        log_error(e, {'function': 'verify_behavior_exists', 'project_id': project_id, 'behavior_id': behavior_id})
        return False


def update_behavior_endpoint(table, project_id, behavior_id, endpoint_id):
    """Update behavior with endpoint reference."""
    try:
        # Get current behavior
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'BEHAVIOR#{behavior_id}'
            }
        )
        
        if 'Item' in response:
            behavior = response['Item']
            api_endpoints = behavior.get('apiEndpoints', [])
            api_endpoints.append(endpoint_id)
            
            # Update behavior
            table.update_item(
                Key={
                    'PK': f'PROJECT#{project_id}',
                    'SK': f'BEHAVIOR#{behavior_id}'
                },
                UpdateExpression='SET apiEndpoints = :apiEndpoints, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':apiEndpoints': api_endpoints,
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        log_error(e, {'function': 'update_behavior_endpoint', 'project_id': project_id, 'behavior_id': behavior_id})
        # Continue even if behavior update fails


def update_project_endpoint_count(table, user_id, project_id):
    """Update the project's endpoint count in metadata."""
    try:
        # Get current project
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROJECT#{project_id}'
            }
        )
        
        if 'Item' in response:
            project = response['Item']
            metadata = project.get('metadata', {})
            metadata['totalEndpoints'] = metadata.get('totalEndpoints', 0) + 1
            
            # Update project
            table.update_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'PROJECT#{project_id}'
                },
                UpdateExpression='SET metadata = :metadata, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':metadata': metadata,
                    ':updatedAt': datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        log_error(e, {'function': 'update_project_endpoint_count', 'user_id': user_id, 'project_id': project_id})
        # Continue even if metadata update fails 