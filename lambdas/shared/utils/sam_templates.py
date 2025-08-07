"""
SAM Template Generation Utilities

This module provides utilities for generating SAM templates
and managing function configurations.
"""

import yaml
import os
from typing import Dict, List, Any


def generate_function_template(
    function_name: str,
    code_uri: str,
    handler: str = "app.lambda_handler",
    runtime: str = "python3.9",
    timeout: int = 30,
    memory_size: int = 512,
    environment_variables: Dict[str, str] = None,
    policies: List[str] = None,
    events: List[Dict[str, Any]] = None,
    layers: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a SAM function template.
    
    Args:
        function_name: Name of the function
        code_uri: Path to function code
        handler: Lambda handler function
        runtime: Python runtime version
        timeout: Function timeout in seconds
        memory_size: Memory allocation in MB
        environment_variables: Environment variables
        policies: IAM policies to attach
        events: API Gateway events
        layers: Lambda layers to use
        
    Returns:
        SAM function template dictionary
    """
    template = {
        "Type": "AWS::Serverless::Function",
        "Properties": {
            "FunctionName": f"${{ResourcePrefix}}-{function_name}",
            "CodeUri": code_uri,
            "Handler": handler,
            "Runtime": runtime,
            "Timeout": timeout,
            "MemorySize": memory_size,
            "Environment": {
                "Variables": environment_variables or {}
            },
            "Tags": {
                "Project": "valthera",
                "Environment": "${Environment}",
                "ManagedBy": "SAM"
            }
        }
    }
    
    if policies:
        template["Properties"]["Policies"] = policies
        
    if events:
        template["Properties"]["Events"] = events
        
    if layers:
        template["Properties"]["Layers"] = layers
        
    return template


def generate_domain_template(
    domain_name: str,
    functions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a domain-specific SAM template.
    
    Args:
        domain_name: Name of the domain (e.g., 'account', 'concepts')
        functions: List of function configurations
        
    Returns:
        Domain SAM template dictionary
    """
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Transform": "AWS::Serverless-2016-10-31",
        "Description": f"Valthera {domain_name.title()} Domain Functions",
        "Resources": {}
    }
    
    for function_config in functions:
        function_name = function_config["name"]
        template["Resources"][f"{function_name}Function"] = (
            generate_function_template(**function_config)
        )
        
    return template


def save_template(template: Dict[str, Any], file_path: str):
    """
    Save a SAM template to a YAML file.
    
    Args:
        template: SAM template dictionary
        file_path: Path to save the template
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)


def load_template(file_path: str) -> Dict[str, Any]:
    """
    Load a SAM template from a YAML file.
    
    Args:
        file_path: Path to the template file
        
    Returns:
        SAM template dictionary
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f) 