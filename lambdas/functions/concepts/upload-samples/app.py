import boto3
import uuid
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from valthera_core import (
    log_execution_time, 
    log_request_info, 
    log_error, 
    log_response_info,
    get_user_id_from_event
)
from valthera_core import validate_file_size, validate_file_type
from valthera_core import success_response, error_response, not_found_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Upload behavior samples to S3 and update metadata."""
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
        
        # Verify behavior exists and belongs to project
        if not verify_behavior_exists(project_id, behavior_id):
            return not_found_response('Behavior', behavior_id)
        
        # Parse request body (multipart form data)
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        # Parse multipart form data
        try:
            file_data = parse_multipart_data(event['body'], event.get('headers', {}))
        except Exception as e:
            return error_response(f'Invalid file data: {str(e)}', 400)
        
        if not file_data:
            return error_response('No file data found', 400)
        
        # Validate file
        file_name = file_data.get('filename', 'unknown')
        file_content = file_data.get('content', b'')
        
        # Validate file size
        is_valid_size, size_error = validate_file_size(len(file_content))
        if not is_valid_size:
            return error_response(size_error, 400, 'VALIDATION_ERROR')
        
        # Validate file type
        is_valid_type, type_error = validate_file_type(file_name)
        if not is_valid_type:
            return error_response(type_error, 400, 'VALIDATION_ERROR')
        
        # Generate S3 key for behavior sample
        sample_id = str(uuid.uuid4())
        s3_key = f"behaviors/{project_id}/{behavior_id}/samples/{sample_id}_{file_name}"
        
        # Upload to S3
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket=Config.VIDEO_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType='video/mp4'
        )
        
        # Create sample metadata
        sample_metadata = {
            'sampleId': sample_id,
            'fileName': file_name,
            'fileSize': len(file_content),
            'uploadDate': datetime.utcnow().isoformat(),
            's3Key': s3_key,
            'processingStatus': 'pending',
            'metadata': {
                'width': None,
                'height': None,
                'fps': None,
                'format': file_name.split('.')[-1] if '.' in file_name else 'unknown'
            }
        }
        
        # Update behavior with new sample
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        # Get current behavior
        behavior_response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            }
        )
        
        if 'Item' not in behavior_response:
            return not_found_response('Behavior', behavior_id)
        
        behavior = behavior_response['Item']
        linked_videos = behavior.get('linkedVideos', [])
        linked_videos.append(sample_metadata)
        
        # Update behavior in DynamoDB
        table.update_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{behavior_id}'
            },
            UpdateExpression='SET linkedVideos = :linkedVideos, sampleCount = :sampleCount, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':linkedVideos': linked_videos,
                ':sampleCount': len(linked_videos),
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        # Return success response
        response_data = {
            'sampleId': sample_id,
            'fileName': file_name,
            'fileSize': len(file_content),
            'uploadDate': sample_metadata['uploadDate'],
            's3Key': s3_key,
            'processingStatus': 'pending',
            'metadata': sample_metadata['metadata']
        }
        
        response = success_response(response_data, 201)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'upload_samples', 'event': event})
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
                'SK': f'CONCEPT#{behavior_id}'
            }
        )
        
        return 'Item' in response
    except Exception as e:
        log_error(e, {'function': 'verify_behavior_exists', 'project_id': project_id, 'behavior_id': behavior_id})
        return False


def parse_multipart_data(body, headers):
    """Parse multipart form data from request body."""
    # This is a simplified parser - in production you'd use a proper library
    try:
        # For now, assume the body contains the file data directly
        # In a real implementation, you'd parse the multipart boundary
        content_type = headers.get('content-type', '')
        
        if 'multipart/form-data' in content_type:
            # Extract boundary
            boundary = content_type.split('boundary=')[-1]
            
            # Parse multipart data
            parts = body.split(f'--{boundary}')
            
            for part in parts:
                if 'filename=' in part and 'Content-Type:' in part:
                    # Extract filename
                    filename_start = part.find('filename="') + 10
                    filename_end = part.find('"', filename_start)
                    filename = part[filename_start:filename_end]
                    
                    # Extract content
                    content_start = part.find('\r\n\r\n') + 4
                    content_end = part.find(f'\r\n--{boundary}', content_start)
                    if content_end == -1:
                        content_end = part.find('\r\n--', content_start)
                    
                    content = part[content_start:content_end]
                    
                    return {
                        'filename': filename,
                        'content': content.encode('utf-8') if isinstance(content, str) else content
                    }
        
        # Fallback: assume body is the file content
        return {
            'filename': 'behavior_sample.mp4',
            'content': body.encode('utf-8') if isinstance(body, str) else body
        }
        
    except Exception as e:
        log_error(e, {'function': 'parse_multipart_data'})
        return None 