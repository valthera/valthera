import re
from typing import Dict, Any, List


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate required fields and return list of missing fields."""
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing.append(field)
    return missing


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string.lower()))


def validate_project_name(name: str) -> tuple[bool, str]:
    """Validate project name format and length."""
    if not name or len(name.strip()) == 0:
        return False, "Project name cannot be empty"
    
    if len(name) > 100:
        return False, "Project name cannot exceed 100 characters"
    
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False, "Project name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return True, ""


def validate_behavior_name(name: str) -> tuple[bool, str]:
    """Validate behavior name format and length."""
    if not name or len(name.strip()) == 0:
        return False, "Behavior name cannot be empty"
    
    if len(name) > 100:
        return False, "Behavior name cannot exceed 100 characters"
    
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False, "Behavior name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return True, ""


def validate_concept_name(name: str) -> tuple[bool, str]:
    """Validate concept name format and length."""
    if not name or len(name.strip()) == 0:
        return False, "Concept name cannot be empty"
    
    if len(name) > 100:
        return False, "Concept name cannot exceed 100 characters"
    
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False, "Concept name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return True, ""


def validate_file_size(file_size: int, max_size_mb: int = 100) -> tuple[bool, str]:
    """Validate file size in bytes."""
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File size exceeds maximum limit of {max_size_mb}MB"
    return True, ""


def validate_file_type(filename: str, allowed_extensions: List[str] = None) -> tuple[bool, str]:
    """Validate file type by extension."""
    if allowed_extensions is None:
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if f'.{file_ext}' not in allowed_extensions:
        return False, f"File type .{file_ext} is not allowed. Allowed types: {', '.join(allowed_extensions)}"
    return True, ""


def validate_user_id(user_id: str) -> bool:
    """Validate user ID format."""
    if not user_id or not isinstance(user_id, str):
        return False
    return len(user_id) > 0 and len(user_id) <= 128


def validate_project_id(project_id: str) -> bool:
    """Validate project ID format."""
    if not project_id or not isinstance(project_id, str):
        return False
    return len(project_id) > 0 and len(project_id) <= 128


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key or not isinstance(api_key, str):
        return False
    # API keys should be alphanumeric and at least 16 characters
    return len(api_key) >= 16 and api_key.isalnum() 