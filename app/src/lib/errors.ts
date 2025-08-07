export class ApiError extends Error {
  public statusCode: number;
  public code?: string;

  constructor(message: string, statusCode: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

export const handleApiError = (error: any): ApiError => {
  if (error instanceof ApiError) return error;
  
  // Handle different error types
  if (error.name === 'ValidationError') {
    return new ApiError(error.message, 400, 'VALIDATION_ERROR');
  }
  
  if (error.name === 'NotFoundError') {
    return new ApiError(error.message, 404, 'NOT_FOUND');
  }
  
  if (error.name === 'UnauthorizedError') {
    return new ApiError(error.message, 401, 'UNAUTHORIZED');
  }
  
  return new ApiError('Internal server error', 500, 'INTERNAL_ERROR');
};

export const isNetworkError = (error: any): boolean => {
  return error.code === 'NETWORK_ERROR' || error.message.includes('fetch');
};

// Specific error types for better error handling
export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class UnauthorizedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class ConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConflictError';
  }
}

// Error codes for consistent error handling
export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  CONFLICT: 'CONFLICT',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
} as const;

// Error messages for common scenarios
export const ERROR_MESSAGES = {
  PROJECT_NOT_FOUND: 'Project not found',
  BEHAVIOR_NOT_FOUND: 'Behavior not found',
  DATASOURCE_NOT_FOUND: 'Data source not found',
  TRAINING_JOB_NOT_FOUND: 'Training job not found',
  ENDPOINT_NOT_FOUND: 'API endpoint not found',
  INVALID_PROJECT_NAME: 'Invalid project name',
  INVALID_BEHAVIOR_NAME: 'Invalid behavior name',
  FILE_TOO_LARGE: 'File size exceeds maximum limit',
  INVALID_FILE_TYPE: 'Invalid file type',
  UNAUTHORIZED_ACCESS: 'Unauthorized access to resource',
  INSUFFICIENT_PERMISSIONS: 'Insufficient permissions',
  RESOURCE_CONFLICT: 'Resource already exists',
  TRAINING_IN_PROGRESS: 'Training job already in progress',
  INVALID_API_KEY: 'Invalid API key',
  RATE_LIMIT_EXCEEDED: 'Rate limit exceeded',
} as const; 