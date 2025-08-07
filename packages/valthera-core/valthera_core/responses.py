import json
from typing import Any, Dict
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_cors_headers() -> Dict[str, str]:
    """Standard CORS headers for all responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE,PATCH',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Access-Control-Allow-Origin,Access-Control-Allow-Credentials'
    }


def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Standard success response format"""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(data, cls=DecimalEncoder)
    }


def error_response(message: str, status_code: int = 500, error_code: str = None) -> Dict[str, Any]:
    """Standard error response format"""
    error_body = {'error': message}
    if error_code:
        error_body['code'] = error_code
    
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(error_body, cls=DecimalEncoder)
    }


def options_response() -> Dict[str, Any]:
    """Standard OPTIONS response for CORS preflight"""
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': ''
    }


def validation_error_response(missing_fields: list, message: str = "Validation failed") -> Dict[str, Any]:
    """Standard validation error response"""
    error_body = {
        'error': message,
        'code': 'VALIDATION_ERROR',
        'missing_fields': missing_fields
    }
    
    return {
        'statusCode': 400,
        'headers': get_cors_headers(),
        'body': json.dumps(error_body)
    }


def not_found_response(resource_type: str, resource_id: str) -> Dict[str, Any]:
    """Standard not found response"""
    message = f"{resource_type} with id '{resource_id}' not found"
    return error_response(message, 404, 'NOT_FOUND')


def unauthorized_response(message: str = "Unauthorized access") -> Dict[str, Any]:
    """Standard unauthorized response"""
    return error_response(message, 401, 'UNAUTHORIZED')


def forbidden_response(message: str = "Insufficient permissions") -> Dict[str, Any]:
    """Standard forbidden response"""
    return error_response(message, 403, 'FORBIDDEN')


def conflict_response(message: str = "Resource conflict") -> Dict[str, Any]:
    """Standard conflict response"""
    return error_response(message, 409, 'CONFLICT') 