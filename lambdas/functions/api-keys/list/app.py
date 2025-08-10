"""
List API Keys Lambda Function

This function lists all API keys for the authenticated user.
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'shared', 'valthera-core-layer', 'python'))

from valthera_core.auth import require_auth
from valthera_core.api_keys import APIKeyService, create_storage
from valthera_core.responses import success_response, error_response


def lambda_handler(event, context):
    """Lambda handler for listing API keys."""
    try:
        # Authenticate user
        key_record = require_auth(event, required_scopes=['read'])
        user_id = key_record.user_id
        
        # Create API key service
        storage = create_storage()
        service = APIKeyService(storage)
        
        # List user's API keys
        keys = service.list_user_keys(user_id)
        
        # Convert to safe format (no hashes or secrets)
        safe_keys = []
        for key in keys:
            safe_keys.append({
                'key_id': key.key_id,
                'name': key.name,
                'scopes': key.scopes,
                'created_at': key.created_at,
                'expires_at': key.expires_at,
                'revoked': key.revoked,
                'is_valid': key.is_valid,
                'is_expired': key.is_expired
            })
        
        return success_response({
            'message': 'API keys retrieved successfully',
            'keys': safe_keys,
            'count': len(safe_keys)
        })
        
    except Exception as e:
        return error_response(f"Failed to list API keys: {str(e)}")


# For local testing
if __name__ == "__main__":
    # Mock event for local testing
    test_event = {
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