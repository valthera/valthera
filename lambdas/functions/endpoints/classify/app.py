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
from valthera_core import validate_file_size, validate_file_type, validate_api_key
from valthera_core import success_response, error_response, not_found_response, unauthorized_response
from valthera_core import Config


@log_execution_time
def lambda_handler(event, context):
    """Classify video using a trained endpoint."""
    try:
        log_request_info(event)
        
        # Get endpoint ID from path parameters
        endpoint_id = event.get('pathParameters', {}).get('endpointId')
        if not endpoint_id:
            return error_response('Endpoint ID is required', 400)
        
        # Validate API key
        api_key = get_api_key_from_event(event)
        if not api_key or not validate_api_key(api_key):
            return unauthorized_response('Invalid API key')
        
        # Get endpoint from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        # Query for endpoint using scan (since we removed GSIs)
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': f'ENDPOINT#{endpoint_id}'
            }
        )
        
        if not response.get('Items'):
            return not_found_response('Endpoint', endpoint_id)
        
        endpoint = response['Items'][0]
        
        # Check if endpoint is ready
        if endpoint.get('status') != 'ready':
            return error_response('Endpoint is not ready for classification', 400, 'ENDPOINT_NOT_READY')
        
        # Parse request body (multipart form data)
        if not event.get('body'):
            return error_response('Request body is required', 400)
        
        # Parse multipart form data
        try:
            file_data = parse_multipart_data(event['body'], event.get('headers', {}))
        except Exception as e:
            return error_response(f'Invalid file data: {str(e)}', 400)
        
        if not file_data:
            return error_response('No video file found', 400)
        
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
        
        # Perform classification (simulated for now)
        classification_result = perform_classification(endpoint, file_content)
        
        # Update usage metrics
        update_endpoint_usage(table, endpoint, classification_result)
        
        # Return classification result
        response_data = {
            'prediction': classification_result['prediction'],
            'confidence': classification_result['confidence'],
            'endpointId': endpoint_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = success_response(response_data)
        log_response_info(response)
        return response
        
    except Exception as e:
        log_error(e, {'function': 'classify_video', 'event': event})
        return error_response('Internal server error', 500)


def get_api_key_from_event(event):
    """Extract API key from request headers."""
    try:
        headers = event.get('headers', {})
        api_key = headers.get('X-API-Key') or headers.get('x-api-key')
        return api_key
    except Exception as e:
        log_error(e, {'function': 'get_api_key_from_event'})
        return None


def perform_classification(endpoint, video_content):
    """Perform video classification using the endpoint."""
    try:
        # This is a simulated classification
        # In production, you would:
        # 1. Load the trained model from S3
        # 2. Preprocess the video
        # 3. Run inference
        # 4. Return predictions
        
        # For now, return a simulated result
        import random
        
        # Get behavior name for more realistic predictions
        behavior_id = endpoint.get('behaviorId', '')
        behavior_name = get_behavior_name(endpoint.get('PK', '').replace('PROJECT#', ''), behavior_id)
        
        # Generate realistic predictions based on behavior
        if 'pick' in behavior_name.lower() or 'place' in behavior_name.lower():
            predictions = ['Pick and Place', 'Object Grasping', 'Idle', 'Assembly']
        elif 'grasp' in behavior_name.lower():
            predictions = ['Object Grasping', 'Pick and Place', 'Idle', 'Failed Grasp']
        elif 'assembly' in behavior_name.lower():
            predictions = ['Assembly', 'Screw Insertion', 'Part Alignment', 'Idle']
        else:
            predictions = ['Idle', 'Active', 'Completed', 'Error']
        
        prediction = random.choice(predictions)
        confidence = random.uniform(0.7, 0.95)  # 70-95% confidence
        
        return {
            'prediction': prediction,
            'confidence': round(confidence, 3)
        }
        
    except Exception as e:
        log_error(e, {'function': 'perform_classification'})
        return {
            'prediction': 'Error',
            'confidence': 0.0
        }


def get_behavior_name(project_id, behavior_id):
    """Get behavior name for more realistic predictions."""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.MAIN_TABLE)
        
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'BEHAVIOR#{behavior_id}'
            }
        )
        
        if 'Item' in response:
            return response['Item'].get('name', 'Unknown Behavior')
        
        return 'Unknown Behavior'
    except Exception as e:
        log_error(e, {'function': 'get_behavior_name'})
        return 'Unknown Behavior'


def update_endpoint_usage(table, endpoint, classification_result):
    """Update endpoint usage metrics."""
    try:
        project_id = endpoint['PK'].replace('PROJECT#', '')
        endpoint_id = endpoint['SK'].replace('ENDPOINT#', '')
        
        # Get current usage metrics
        usage_metrics = endpoint.get('usageMetrics', {})
        total_calls = usage_metrics.get('totalCalls', 0) + 1
        
        # Calculate error rate (simplified)
        error_rate = usage_metrics.get('errorRate', 0)
        if classification_result['prediction'] == 'Error':
            error_rate = (error_rate * (total_calls - 1) + 1) / total_calls
        
        # Update endpoint
        table.update_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'ENDPOINT#{endpoint_id}'
            },
            UpdateExpression='SET usageMetrics = :usageMetrics',
            ExpressionAttributeValues={
                ':usageMetrics': {
                    'totalCalls': total_calls,
                    'lastUsed': datetime.utcnow().isoformat(),
                    'errorRate': round(error_rate, 3)
                }
            }
        )
    except Exception as e:
        log_error(e, {'function': 'update_endpoint_usage'})
        # Continue even if usage update fails


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
            'filename': 'classification_video.mp4',
            'content': body.encode('utf-8') if isinstance(body, str) else body
        }
        
    except Exception as e:
        log_error(e, {'function': 'parse_multipart_data'})
        return None 