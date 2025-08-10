"""
Revoke API Key Lambda Function

This function revokes an API key for the authenticated user.
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'shared', 'valthera-core-layer', 'python'))

from valthera_core.auth import require_auth
from valthera_core.api_keys import APIKeyService, create_storage
from valthera_core.responses import success_response, error_response, validation_error_response
from valthera_core.validation import validate_required_fields


def lambda_handler(event, context):
    """Lambda handler for revoking API keys."""
    try:
        # Authenticate user
        key_record = require_auth(event, required_scopes=['write'])
        user_id = key_record.user_id
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['key_id']
        missing_fields = validate_required_fields(body, required_fields)
        if missing_fields:
            return validation_error_response(missing_fields)
        
        key_id = body['key_id']
        
        # Create API key service
        storage = create_storage()
        service = APIKeyService(storage)
        
        # Get the key to verify ownership
        existing_key = service.storage.get(key_id)
        if not existing_key:
            return error_response('API key not found', status_code=404)
        
        # Verify the key belongs to the authenticated user
        if existing_key.user_id != user_id:
            return error_response('Unauthorized', status_code=403)
        
        # Revoke the key
        service.revoke_key(key_id)
        
        return success_response({
            'message': 'API key revoked successfully',
            'key_id': key_id
        })
        
    except Exception as e:
        return error_response(f"Failed to revoke API key: {str(e)}")


# For local testing
if __name__ == "__main__":
    # Mock event for local testing
    test_event = {
        'body': json.dumps({
            'key_id': 'test-key-id'
        }),
        'headers': {
            'x-api-key': 'test-key'
        }
    }
    
    # Set environment for local testing
    import os
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['DEV_BYPASS'] = 'true'
    os.environ['API_KEYS_TABLE'] = 'test-api-keys'
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2)) 