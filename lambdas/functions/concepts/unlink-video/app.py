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
from valthera_core import get_user_id_from_event
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Unlink a video from a behavior."""
    try:
        log_request_info(event)
        
        # Get project, behavior, and video IDs from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        behavior_id = event.get('pathParameters', {}).get('behaviorId')
        video_id = event.get('pathParameters', {}).get('videoId')
        
        if not project_id or not behavior_id or not video_id:
            return error_response(
                'Project ID, Behavior ID, and Video ID are required', 400
            )
        
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
        
        behavior_item = response['Item']
        
        # Get current linked videos
        current_linked_videos = behavior_item.get('linkedVideos', [])
        
        # Remove video ID from linked videos
        if video_id in current_linked_videos:
            new_linked_videos = [v for v in current_linked_videos if v != video_id]
        else:
            return error_response('Video is not linked to this behavior', 400)
        
        # Update behavior with new linked videos
        update_expression = ("SET linkedVideos = :linkedVideos, "
                           "updatedAt = :updatedAt")
        expression_attribute_values = {
            ':linkedVideos': new_linked_videos,
            ':updatedAt': datetime.utcnow().isoformat()
        }
        
        # Update sample count
        update_expression += ", sampleCount = :sampleCount"
        expression_attribute_values[':sampleCount'] = len(new_linked_videos)
        
        table.update_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        log_response_info({
            'message': 'Video unlinked successfully',
            'behaviorId': behavior_id,
            'videoId': video_id,
            'linkedVideos': new_linked_videos,
            'sampleCount': len(new_linked_videos)
        })
        
        return success_response({
            'message': 'Video unlinked successfully',
            'behaviorId': behavior_id,
            'videoId': video_id,
            'linkedVideos': new_linked_videos,
            'sampleCount': len(new_linked_videos)
        })
        
    except Exception as e:
        log_error(e)
        return error_response(f'Internal server error: {str(e)}', 500)





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
        print(f"Error verifying project ownership: {e}")
        return False 