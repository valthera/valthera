"""
Valthera Core - Shared utilities for Lambda functions
"""

from .config import Config
from .monitoring import (
    log_execution_time,
    log_request_info,
    log_response_info,
    log_error,
    log_dynamodb_operation
)
from .responses import (
    success_response,
    error_response,
    not_found_response,
    unauthorized_response,
    forbidden_response,
    conflict_response,
    validation_error_response,
    options_response,
    get_cors_headers
)
from .validation import (
    validate_required_fields, 
    validate_behavior_name, 
    validate_concept_name,
    validate_project_name,
    validate_file_type,
    validate_file_size
)
from .auth import (
    get_user_id_from_event,
    require_authentication
)
from .aws_clients import (
    get_s3_client,
    get_dynamodb_resource,
    get_dynamodb_client,
    get_sqs_client
)

__version__ = "0.1.0"

__all__ = [
    "Config",
    "log_execution_time",
    "log_request_info", 
    "log_response_info",
    "log_error",
    "log_dynamodb_operation",
    "success_response",
    "error_response",
    "not_found_response",
    "unauthorized_response",
    "forbidden_response",
    "conflict_response",
    "validation_error_response",
    "options_response",
    "get_cors_headers",
    "validate_required_fields",
    "validate_behavior_name",
    "validate_concept_name",
    "validate_project_name",
    "validate_file_type",
    "validate_file_size",
    "get_user_id_from_event",
    "require_authentication",
    "get_s3_client",
    "get_dynamodb_resource",
    "get_dynamodb_client",
    "get_sqs_client"
] 