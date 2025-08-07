"""
Authentication utilities for Lambda functions
"""

from .monitoring import log_error


def get_user_id_from_event(event):
    """Extract user ID from Cognito authorizer context.
    
    Args:
        event: Lambda event object
        
    Returns:
        str: User ID if found, None otherwise
    """
    try:
        # Get user ID from Cognito authorizer
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        
        # Debug: Log the authorizer context to see what's available
        print(f"DEBUG: Authorizer context: {authorizer_context}")
        
        # For Cognito User Pool authorizers, the user info is in the 'claims' object
        claims = authorizer_context.get('claims', {})
        user_id = claims.get('sub') or claims.get('user_id')

        # Fallback for other authorizer types (e.g., Lambda authorizer) or direct testing
        if not user_id:
            user_id = authorizer_context.get('sub') or authorizer_context.get('user_id')
        
        print(f"DEBUG: Extracted user_id: {user_id}")
        
        if not user_id:
            # Fallback to headers if authorizer not available
            user_id = event.get('headers', {}).get('X-User-ID')
            print(f"DEBUG: Fallback user_id from headers: {user_id}")
        
        return user_id
    except Exception as e:
        log_error(e, {'function': 'get_user_id_from_event'})
        return None


def require_authentication(event):
    """Check if user is authenticated and return user ID.
    
    Args:
        event: Lambda event object
        
    Returns:
        str: User ID if authenticated, None otherwise
    """
    user_id = get_user_id_from_event(event)
    if not user_id:
        return None
    return user_id 