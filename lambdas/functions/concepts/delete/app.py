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
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Delete a behavior and all related data."""
    try:
        log_request_info(event)
        
        # Get project and behavior IDs from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        behavior_id = event.get('pathParameters', {}).get('id')
        
        if not project_id or not behavior_id:
            return error_response('Project ID and Behavior ID are required', 400)
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Verify project ownership
        if not verify_project_ownership(user_id, project_id):
            return not_found_response('Project', project_id)
        
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
        
        behavior = response['Item']
        
        # Delete related S3 objects (behavior samples)
        delete_behavior_samples(behavior)
        
        # Delete related endpoints
        delete_related_endpoints(table, project_id, behavior_id)
        
        # Delete the behavior
        table.delete_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            }
        )
        
        # Update project's behavior count
        update_project_behavior_count(table, user_id, project_id, -1)
        
        response_data = success_response({'message': 'Behavior deleted successfully'})
        log_response_info(response_data)
        return response_data
        
    except Exception as e:
        log_error(e, {'function': 'delete_behavior', 'event': event})
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


def delete_behavior_samples(behavior):
    """Delete S3 objects for behavior samples."""
    try:
        s3 = boto3.client('s3')
        linked_videos = behavior.get('linkedVideos', [])
        
        for video in linked_videos:
            s3_key = video.get('s3Key')
            if s3_key:
                try:
                    s3.delete_object(
                        Bucket=Config.VIDEO_BUCKET,
                        Key=s3_key
                    )
                except Exception as e:
                    log_error(e, {'function': 'delete_behavior_samples', 's3_key': s3_key})
                    # Continue even if S3 deletion fails
    except Exception as e:
        log_error(e, {'function': 'delete_behavior_samples'})
        # Continue even if S3 operations fail


def delete_related_endpoints(table, project_id, behavior_id):
    """Delete all endpoints related to this behavior."""
    try:
        # Query for endpoints related to this behavior
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'PROJECT#{project_id}',
                ':sk_prefix': 'ENDPOINT#'
            }
        )
        
        # Delete endpoints that reference this behavior
        for endpoint in response.get('Items', []):
            if endpoint.get('behaviorId') == behavior_id:
                table.delete_item(
                    Key={
                        'PK': endpoint['PK'],
                        'SK': endpoint['SK']
                    }
                )
    except Exception as e:
        log_error(e, {'function': 'delete_related_endpoints', 'project_id': project_id, 'behavior_id': behavior_id})
        # Continue even if endpoint deletion fails


def update_project_behavior_count(table, user_id, project_id, increment=0):
    """Update the project's behavior count in metadata."""
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
            current_count = metadata.get('totalBehaviors', 0)
            metadata['totalBehaviors'] = max(0, current_count + increment)
            
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
        log_error(e, {'function': 'update_project_behavior_count', 'user_id': user_id, 'project_id': project_id})
        # Continue even if metadata update fails 