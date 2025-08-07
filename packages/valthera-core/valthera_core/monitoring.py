import json
import time
from functools import wraps

def log_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            print(f"Function {func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Function {func.__name__} failed after {execution_time:.2f}s: {str(e)}")
            raise
    return wrapper

def log_request_info(event):
    """Log request information for debugging"""
    print(f"Request method: {event.get('httpMethod')}")
    print(f"Request path: {event.get('path')}")
    print(f"Request headers: {json.dumps(event.get('headers', {}), indent=2)}")
    if event.get('body'):
        print(f"Request body: {event.get('body')}")

def log_response_info(response):
    """Log response information for debugging"""
    print(f"Response status: {response.get('statusCode')}")
    print(f"Response headers: {json.dumps(response.get('headers', {}), indent=2)}")
    if response.get('body'):
        print(f"Response body: {response.get('body')}")

def log_error(error, context=None):
    """Log error information with context"""
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': time.time()
    }
    if context:
        error_info['context'] = context
    
    print(f"ERROR: {json.dumps(error_info, indent=2)}")

def log_dynamodb_operation(operation, table_name, key_info=None):
    """Log DynamoDB operation for debugging"""
    operation_info = {
        'operation': operation,
        'table': table_name,
        'timestamp': time.time()
    }
    if key_info:
        operation_info['key_info'] = key_info
    
    print(f"DynamoDB: {json.dumps(operation_info, indent=2)}") 