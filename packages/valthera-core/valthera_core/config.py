import os


class Config:
    """Shared configuration for Lambda functions"""
    
    # DynamoDB Tables
    MAIN_TABLE = os.environ.get('MAIN_TABLE_NAME', 'valthera-dev-main')
    USER_TABLE = os.environ.get('USER_TABLE_NAME', 'valthera-dev-users')
    VIDEO_TABLE = os.environ.get('VIDEO_TABLE_NAME', 'valthera-dev-videos')
    
    # S3 Buckets
    VIDEO_BUCKET = os.environ.get('VIDEO_BUCKET_NAME', 'valthera-dev-videos')
    MODEL_BUCKET = os.environ.get('MODEL_BUCKET_NAME', 'valthera-dev-models')
    
    # S3 Endpoints (for local development)
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', None)
    AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', None)
    
    # DynamoDB Endpoints (for local development)
    DYNAMODB_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', None)
    
    # SQS Configuration
    SQS_ENDPOINT_URL = os.environ.get('SQS_ENDPOINT_URL', None)
    
    # SQS Queues
    TRAINING_QUEUE = os.environ.get('TRAINING_QUEUE_URL', '')
    VIDEO_PROCESSOR_QUEUE = os.environ.get('VIDEO_PROCESSOR_QUEUE_URL', '')
    
    # API Configuration
    API_KEY_HEADER = 'X-API-Key'
    
    # Validation Limits
    MAX_PROJECT_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_FILE_SIZE_MB = 100
    
    @classmethod
    def get_table_name(cls, table_type: str) -> str:
        """Get table name by type"""
        table_map = {
            'main': cls.MAIN_TABLE,
            'user': cls.USER_TABLE,
            'video': cls.VIDEO_TABLE
        }
        return table_map.get(table_type, cls.MAIN_TABLE)
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return os.environ.get('ENVIRONMENT', 'dev') == 'production'
    
    @classmethod
    def get_environment(cls) -> str:
        """Get current environment"""
        return os.environ.get('ENVIRONMENT', 'dev')
    
    @classmethod
    def get_log_level(cls) -> str:
        """Get log level for the environment"""
        return os.environ.get('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_cors_origin(cls) -> str:
        """Get CORS origin for the environment"""
        if cls.is_production():
            return os.environ.get('CORS_ORIGIN', 'https://yourdomain.com')
        else:
            return '*'
    
    @classmethod
    def get_rate_limit(cls) -> int:
        """Get rate limit for API calls"""
        return int(os.environ.get('RATE_LIMIT', '1000'))
    
    @classmethod
    def get_timeout_seconds(cls) -> int:
        """Get Lambda timeout in seconds"""
        return int(os.environ.get('TIMEOUT_SECONDS', '30')) 