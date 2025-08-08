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
    """Delete a data source and all its files from S3."""
    try:
        log_request_info(event)
        
        # Get data source ID from path parameters  
        datasource_id = event.get('pathParameters', {}).get('datasourceId')
        if not datasource_id:
            return error_response('Data source ID is required', 400)
        
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
        
        # Delete all files from S3
        s3_client = boto3.client('s3')
        deleted_files = []
        failed_deletions = []
        
        for file_metadata in files:
            s3_key = file_metadata.get('s3Key')
            if s3_key:
                # Verify the S3 key belongs to this user and data source
                expected_prefix = f"users/{user_id}/data-sources/{datasource_id}/"
                if s3_key.startswith(expected_prefix):
                    try:
                        s3_client.delete_object(Bucket=Config.VIDEO_BUCKET, Key=s3_key)
                        deleted_files.append({
                            'fileName': file_metadata.get('fileName'),
                            's3Key': s3_key
                        })
                    except Exception as e:
                        log_error(e, {'function': 'delete_datasource', 's3_key': s3_key})
                        failed_deletions.append({
                            'fileName': file_metadata.get('fileName'),
                            's3Key': s3_key,
                            'error': str(e)
                        })
        
        # Delete any remaining objects in the data source folder
        try:
            folder_prefix = f"users/{user_id}/data-sources/{datasource_id}/"
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=Config.VIDEO_BUCKET, Prefix=folder_prefix):
                if 'Contents' in page:
                    objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                    if objects_to_delete:
                        s3_client.delete_objects(
                            Bucket=Config.VIDEO_BUCKET,
                            Delete={'Objects': objects_to_delete}
                        )
        except Exception as e:
            log_error(e, {'function': 'delete_datasource', 'folder_cleanup': folder_prefix})
        
        # Delete data source from DynamoDB
        try:
            table.delete_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'DATASOURCE#{datasource_id}'
                }
            )
        except Exception as e:
            log_error(e, {'function': 'delete_datasource', 'dynamodb_delete': datasource_id})
            return error_response('Failed to delete data source from database', 500)
        
        # Return success response
        response_data = {
            'message': 'Data source deleted successfully',
            'deletedDataSource': {
                'id': datasource_id,
                'name': datasource.get('name'),
                'filesDeleted': len(deleted_files),
                'failedDeletions': len(failed_deletions)
            }
        }
        
        if failed_deletions:
            response_data['failedDeletions'] = failed_deletions
        
        response = success_response(response_data, 200)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'delete_datasource', 'event': event})
        return error_response('Internal server error', 500)


