"""
Function Builder Utilities

This module provides utilities for building and packaging
Lambda functions with proper dependencies.
"""

import os
import subprocess
import shutil
from typing import Dict


def build_function_dependencies(function_path: str) -> bool:
    """
    Ensure function dependencies via requirements.txt for AWS SAM.

    If a requirements.txt is missing, scaffold a minimal one.
    Then install packages into a local .venv folder for local testing,
    while SAM will vendor deps during `sam build`.

    Args:
        function_path: Path to the function directory

    Returns:
        True if successful, False otherwise
    """
    try:
        requirements_path = os.path.join(function_path, "requirements.txt")
        if not os.path.exists(requirements_path):
            print(f"requirements.txt not found in {function_path}; creating a minimal one")
            with open(requirements_path, "w") as f:
                f.write("boto3==1.40.4\n")
                f.write("botocore==1.40.4\n")
                f.write("jmespath==1.0.1\n")
                f.write("python-dateutil==2.9.0.post0\n")
                f.write("s3transfer==0.13.1\n")
                f.write("six==1.17.0\n")
                f.write("urllib3>=1.21.1,<3\n")

        venv_dir = os.path.join(function_path, ".venv")
        os.makedirs(venv_dir, exist_ok=True)

        subprocess.run(
            ["pip", "install", "-r", requirements_path, "-t", venv_dir],
            cwd=function_path,
            check=True,
        )

        print(f"Dependencies prepared for {function_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies for {function_path}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error preparing dependencies for {function_path}: {e}")
        return False


def package_function(function_path: str, output_path: str) -> bool:
    """
    Package a function for deployment.
    
    Args:
        function_path: Path to the function directory
        output_path: Path to save the package
        
    Returns:
        True if packaging successful, False otherwise
    """
    try:
        # Create output directory
        os.makedirs(output_path, exist_ok=True)
        
        # Copy function code
        app_file = os.path.join(function_path, "app.py")
        if os.path.exists(app_file):
            shutil.copy2(app_file, output_path)
        
        # Copy requirements.txt if it exists
        requirements_file = os.path.join(function_path, "requirements.txt")
        if os.path.exists(requirements_file):
            shutil.copy2(requirements_file, output_path)
        
        # Copy any other necessary files
        for file_name in ["README.md", "function.yaml"]:
            file_path = os.path.join(function_path, file_name)
            if os.path.exists(file_path):
                shutil.copy2(file_path, output_path)
        
        print(f"Successfully packaged {function_path} to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error packaging {function_path}: {e}")
        return False


def build_all_functions(functions_dir: str) -> Dict[str, bool]:
    """
    Build all functions in the functions directory.
    
    Args:
        functions_dir: Path to the functions directory
        
    Returns:
        Dictionary mapping function paths to build success status
    """
    results = {}
    
    for domain_dir in os.listdir(functions_dir):
        domain_path = os.path.join(functions_dir, domain_dir)
        if not os.path.isdir(domain_path):
            continue
            
        for function_dir in os.listdir(domain_path):
            function_path = os.path.join(domain_path, function_dir)
            if not os.path.isdir(function_path):
                continue
                
            print(f"Building function: {function_path}")
            success = build_function_dependencies(function_path)
            results[function_path] = success
            
    return results


def create_function_structure(
    function_name: str,
    domain: str,
    base_path: str = "functions"
) -> str:
    """
    Create a new function directory structure.
    
    Args:
        function_name: Name of the function
        domain: Domain name (e.g., 'account', 'concepts')
        base_path: Base path for functions
        
    Returns:
        Path to the created function directory
    """
    function_path = os.path.join(base_path, domain, function_name)
    os.makedirs(function_path, exist_ok=True)
    
    # Create app.py template
    app_template = '''import json
from valthera_core import auth, responses, monitoring

def lambda_handler(event, context):
    """Standard Lambda handler with error handling and logging."""
    try:
        # Get current user
        user = auth.get_current_user(event)
        
        # Log request
        monitoring.log_request(event, user)
        
        # Route to appropriate handler based on HTTP method
        method = event.get('httpMethod', 'GET')
        
        if method == 'GET':
            return handle_get(event, context, user)
        elif method == 'POST':
            return handle_post(event, context, user)
        elif method == 'PUT':
            return handle_put(event, context, user)
        elif method == 'DELETE':
            return handle_delete(event, context, user)
        else:
            return responses.method_not_allowed()
            
    except Exception as e:
        monitoring.log_error(e)
        return responses.internal_error(str(e))

def handle_get(event, context, user):
    """Handle GET requests."""
    # Implementation specific to function
    return responses.success_response({"message": "GET not implemented"})

def handle_post(event, context, user):
    """Handle POST requests."""
    # Implementation specific to function
    return responses.success_response({"message": "POST not implemented"})

def handle_put(event, context, user):
    """Handle PUT requests."""
    # Implementation specific to function
    return responses.success_response({"message": "PUT not implemented"})

def handle_delete(event, context, user):
    """Handle DELETE requests."""
    # Implementation specific to function
    return responses.success_response({"message": "DELETE not implemented"})
'''
    
    with open(os.path.join(function_path, "app.py"), "w") as f:
        f.write(app_template)
    
    # Create requirements.txt template (SAM-friendly)
    requirements_txt = """boto3==1.40.4
botocore==1.40.4
jmespath==1.0.1
python-dateutil==2.9.0.post0
s3transfer==0.13.1
six==1.17.0
urllib3>=1.21.1,<3
"""

    with open(os.path.join(function_path, "requirements.txt"), "w") as f:
        f.write(requirements_txt)
    
    # Create README.md template
    readme_template = f'''# {function_name}

This Lambda function handles {function_name} operations.

## Development

```bash
cd {function_path}
pip install -r requirements.txt -t .venv
pytest
```

## Deployment

This function is deployed as part of the SAM template.
'''
    
    with open(os.path.join(function_path, "README.md"), "w") as f:
        f.write(readme_template)
    
    # Create tests directory
    tests_path = os.path.join(function_path, "tests")
    os.makedirs(tests_path, exist_ok=True)
    
    with open(os.path.join(tests_path, "__init__.py"), "w") as f:
        f.write("# Tests for {function_name}\n")
    
    return function_path 