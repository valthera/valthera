"""
Create API Key Lambda Function

This function creates new API keys for users using the modular API key system.
"""

import json
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'shared', 'valthera-core-layer', 'python'))

from valthera_core.auth import require_auth
from valthera_core.api_keys import APIKeyService, create_storage
from valthera_core.responses import success_response, error_response, validation_error_response
from valthera_core.validation import validate_required_fields


def lambda_handler(event, context):
    """Lambda handler for creating API keys."""
    try:
        # Authenticate user
        key_record = require_auth(event, required_scopes=['write'])
        user_id = key_record.user_id
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['name', 'scopes']
        missing_fields = validate_required_fields(body, required_fields)
        if missing_fields:
            return validation_error_response(missing_fields)
        
        # Extract parameters
        name = body['name']
        scopes = body['scopes']
        expires_in_days = body.get('expires_in_days')
        
        # Validate scopes
        if not isinstance(scopes, list) or not scopes:
            return validation_error_response(['scopes must be a non-empty list'])
        
        # Create API key service
        storage = create_storage()
        service = APIKeyService(storage)
        
        # Create the API key
        display_key, key_record = service.create_key(
            user_id=user_id,
            name=name,
            scopes=scopes,
            expires_in_days=expires_in_days
        )
        
        # Return success response (display key only shown once)
        return success_response({
            'message': 'API key created successfully',
            'key_id': key_record.key_id,
            'display_key': display_key,  # Only shown once!
            'name': key_record.name,
            'scopes': key_record.scopes,
            'created_at': key_record.created_at,
            'expires_at': key_record.expires_at
        })
        
    except Exception as e:
        return error_response(f"Failed to create API key: {str(e)}")


# For local testing
if __name__ == "__main__":
    # Mock event for local testing
    test_event = {
        'body': json.dumps({
            'name': 'Test Key',
            'scopes': ['read', 'write'],
            'expires_in_days': 30
        }),
        'headers': {
            'x-api-key': 'test-key'
        }
    }
    
    # Set environment for local testing
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['DEV_BYPASS'] = 'true'
    os.environ['API_KEYS_TABLE'] = 'test-api-keys'
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2)) 