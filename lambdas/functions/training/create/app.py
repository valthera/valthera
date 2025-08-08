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
    log_response_info
)
from valthera_core import validate_required_fields
from valthera_core import success_response, error_response, validation_error_response, not_found_response
from valthera_core import Config, get_user_id_from_event


@log_execution_time
def lambda_handler(event, context):
    """Start a new training job for a project."""
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
        required_fields = ['config']
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
        
        # Validate training configuration
        config = data['config']
        if not validate_training_config(config):
            return error_response('Invalid training configuration', 400, 'VALIDATION_ERROR')
        
        # Generate training job ID
        training_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Create training job item for DynamoDB
        training_item = {
            'PK': f'PROJECT#{project_id}',
            'SK': f'TRAINING#{training_id}',
            'GSI1PK': f'TRAINING#{training_id}',
            'GSI1SK': f'PROJECT#{project_id}',
            'status': 'preprocessing',
            'progress': 0,
            'startedAt': timestamp,
            'completedAt': None,
            'logs': ['Training job created', 'Starting preprocessing...'],
            'config': config
        }
        
        # Store in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        table.put_item(Item=training_item)
        
        # Send training job to SQS queue
        sqs = boto3.client('sqs')
        queue_url = Config.TRAINING_QUEUE
        
        if queue_url:
            message_body = {
                'training_id': training_id,
                'project_id': project_id,
                'user_id': user_id,
                'config': config,
                'created_at': timestamp
            }
            
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body)
            )
        
        # Return success response
        response_data = {
            'id': training_id,
            'projectId': project_id,
            'status': 'preprocessing',
            'progress': 0,
            'startedAt': timestamp,
            'completedAt': None,
            'logs': ['Training job created', 'Starting preprocessing...'],
            'config': config
        }
        
        response = success_response(response_data, 201)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'create_training_job', 'event': event})
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


def validate_training_config(config):
    """Validate training configuration."""
    try:
        # Check required config fields
        required_fields = ['modelType', 'hyperparameters', 'dataSources']
        for field in required_fields:
            if field not in config:
                return False
        
        # Validate model type
        valid_model_types = ['vjepa2', 'custom', 'baseline']
        if config['modelType'] not in valid_model_types:
            return False
        
        # Validate hyperparameters
        if not isinstance(config['hyperparameters'], dict):
            return False
        
        # Validate data sources
        if not isinstance(config['dataSources'], list):
            return False
        
        return True
    except Exception as e:
        log_error(e, {'function': 'validate_training_config'})
        return False 