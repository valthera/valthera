"""
AWS Client Helpers - Utilities for creating AWS clients with proper endpoint configuration
"""

import boto3
from .config import Config


def get_s3_client():
    """Get S3 client with proper endpoint configuration for local development."""
    s3_kwargs = {}
    if Config.S3_ENDPOINT_URL:
        s3_kwargs['endpoint_url'] = Config.S3_ENDPOINT_URL
        s3_kwargs['region_name'] = 'us-east-1'
    
    return boto3.client('s3', **s3_kwargs)


def get_dynamodb_resource():
    """Get DynamoDB resource with proper endpoint configuration for local development."""
    dynamodb_kwargs = {}
    if Config.DYNAMODB_ENDPOINT_URL:
        dynamodb_kwargs['endpoint_url'] = Config.DYNAMODB_ENDPOINT_URL
        dynamodb_kwargs['region_name'] = 'us-east-1'
    
    return boto3.resource('dynamodb', **dynamodb_kwargs)


def get_dynamodb_client():
    """Get DynamoDB client with proper endpoint configuration for local development."""
    dynamodb_kwargs = {}
    if Config.DYNAMODB_ENDPOINT_URL:
        dynamodb_kwargs['endpoint_url'] = Config.DYNAMODB_ENDPOINT_URL
        dynamodb_kwargs['region_name'] = 'us-east-1'
    
    return boto3.client('dynamodb', **dynamodb_kwargs)


def get_sqs_client():
    """Get SQS client with proper endpoint configuration for local development."""
    sqs_kwargs = {}
    if Config.SQS_ENDPOINT_URL:
        sqs_kwargs['endpoint_url'] = Config.SQS_ENDPOINT_URL
        sqs_kwargs['region_name'] = 'us-east-1'
    
    return boto3.client('sqs', **sqs_kwargs) 