import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from valthera_core import get_user_id_from_event

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)



def get_cors_headers():
    """Get CORS headers."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
        'Access-Control-Allow-Methods': 'DELETE,GET,OPTIONS,POST,PUT',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Access-Control-Allow-Origin,Access-Control-Allow-Credentials'
    }

def success_response(data, status_code=200):
    """Create a successful response."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def error_response(message, status_code=400, code=None):
    """Create an error response."""
    response_data = {
        'error': message,
        'code': code or 'ERROR'
    }
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(response_data, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    """Link videos to a concept."""
    try:
        print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
        
        # Debug: Print all environment variables
        print(f"All environment variables: {dict(os.environ)}")
        print(f"AWS_ENDPOINT_URL: {os.environ.get('AWS_ENDPOINT_URL')}")
        print(f"MAIN_TABLE_NAME: {os.environ.get('MAIN_TABLE_NAME')}")
        
        # Get project and concept IDs from path parameters
        project_id = event.get('pathParameters', {}).get('projectId')
        concept_id = event.get('pathParameters', {}).get('conceptId')
        
        print(f"Project ID: {project_id}")
        print(f"Concept ID: {concept_id}")
        
        if not project_id or not concept_id:
            return error_response(
                'Project ID and Concept ID are required', 400
            )
        
        # Get user ID from Cognito authorizer
        user_id = get_user_id_from_event(event)
        print(f"User ID: {user_id}")
        
        # For local development, if no auth header is provided, 
        # use a default test user
        if not user_id and (os.environ.get('ENVIRONMENT') == 'dev' or 
                os.environ.get('AWS_ENDPOINT_URL')):
            print("Local development detected - using default test user ID")
            user_id = 'test-user-id'
        
        if not user_id:
            return error_response('User not authenticated', 401, 'UNAUTHORIZED')
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        
        video_ids = body.get('videoIds', [])
        if not video_ids:
            return error_response('videoIds array is required', 400)
        
        print(f"Video IDs to link: {video_ids}")
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Check if we're running locally
        aws_endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        if aws_endpoint_url:
            print(f"Using local DynamoDB endpoint: {aws_endpoint_url}")
            # Check if we're running in SAM local (Docker container)
            is_sam_local = os.environ.get('AWS_SAM_LOCAL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
            print(f"Is SAM local: {is_sam_local}")
            
            # Only replace localhost with host.docker.internal if we're running in Docker
            if aws_endpoint_url.startswith('http://localhost:') and is_sam_local:
                aws_endpoint_url = aws_endpoint_url.replace('localhost', 'host.docker.internal')
                print(f"Updated endpoint URL: {aws_endpoint_url}")
            
            # For local development, use dummy credentials
            dynamodb = boto3.resource(
                'dynamodb', 
                endpoint_url=aws_endpoint_url,
                aws_access_key_id='local',
                aws_secret_access_key='local',
                region_name='us-east-1'
            )
        else:
            print("No AWS_ENDPOINT_URL found - using default AWS DynamoDB")
        
        # Use the main table
        table_name = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
        table = dynamodb.Table(table_name)
        print(f"Using table: {table_name}")
        
        # Check if concept exists
        response = table.get_item(
            Key={
                'PK': f'PROJECT#{project_id}',
                'SK': f'CONCEPT#{concept_id}'
            }
        )
        
        print(f"DynamoDB response: {json.dumps(response, cls=DecimalEncoder)}")
        
        if 'Item' not in response:
            return error_response(f'Concept not found: {concept_id}', 404)
        
        concept_item = response['Item']
        
        # Get current linked videos
        current_linked_videos = concept_item.get('linkedVideos', [])
        print(f"Current linked videos: {current_linked_videos}")
        
        # Add new video IDs (avoid duplicates)
        new_linked_videos = list(set(current_linked_videos + video_ids))
        print(f"New linked videos: {new_linked_videos}")
        
        # Update concept with new linked videos
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
                'SK': f'CONCEPT#{concept_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        print(f"Successfully updated concept with linked videos")
        
        return success_response({
            'message': 'Videos linked successfully',
            'conceptId': concept_id,
            'linkedVideos': new_linked_videos,
            'sampleCount': len(new_linked_videos)
        })
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return error_response('Internal server error', 500) 