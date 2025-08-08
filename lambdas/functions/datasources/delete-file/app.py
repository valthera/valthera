import json
import boto3
import base64
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
from valthera_core import success_response, error_response, not_found_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Delete a file from a data source and S3."""
    try:
        log_request_info(event)
        
        # Get data source ID and file ID from path parameters  
        datasource_id = event.get('pathParameters', {}).get('datasourceId')
        file_id = event.get('pathParameters', {}).get('fileId')
        
        if not datasource_id:
            return error_response('Data source ID is required', 400)
        if not file_id:
            return error_response('File ID is required', 400)
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Get data source from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        response = table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            }
        )
        
        if 'Item' not in response:
            return not_found_response('Data source', datasource_id)
        
        datasource = response['Item']
        files = datasource.get('files', [])
        
        # Find the file to delete
        file_to_delete = None
        file_index = -1
        for i, file_metadata in enumerate(files):
            if file_metadata.get('id') == file_id:
                file_to_delete = file_metadata
                file_index = i
                break
        
        if not file_to_delete:
            return not_found_response('File', file_id)
        
        s3_key = file_to_delete.get('s3Key')
        if not s3_key:
            return error_response('File S3 key not found', 400)
        
        # Verify the S3 key belongs to this user and data source
        expected_prefix = f"users/{user_id}/data-sources/{datasource_id}/"
        if not s3_key.startswith(expected_prefix):
            return error_response('Unauthorized access to file', 403)
        
        # Delete file from S3
        s3_kwargs = {}
        if Config.S3_ENDPOINT_URL:
            s3_kwargs['endpoint_url'] = Config.S3_ENDPOINT_URL
            s3_kwargs['region_name'] = 'us-east-1'
        
        s3_client = boto3.client('s3', **s3_kwargs)
        try:
            s3_client.delete_object(Bucket=Config.VIDEO_BUCKET, Key=s3_key)
        except Exception as e:
            log_error(e, {'function': 'delete_file', 's3_key': s3_key})
            return error_response('Failed to delete file from S3', 500)
        
        # Remove file from files array
        files.pop(file_index)
        
        # Update DynamoDB
        table.update_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'DATASOURCE#{datasource_id}'
            },
            UpdateExpression='SET files = :files, videoCount = :videoCount, totalSize = :totalSize, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':files': files,
                ':videoCount': len(files),
                ':totalSize': sum(f.get('fileSize', 0) for f in files),
                ':updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        # Return success response
        response_data = {
            'message': 'File deleted successfully',
            'deletedFile': {
                'id': file_id,
                'fileName': file_to_delete.get('fileName'),
                'fileSize': file_to_delete.get('fileSize', 0)
            }
        }
        
        response = success_response(response_data, 200)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'delete_file', 'event': event})
        return error_response('Internal server error', 500)


        return None