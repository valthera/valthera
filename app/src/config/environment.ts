export interface EnvironmentConfig {
  apiUrl: string;
  userPoolId: string;
  userPoolClientId: string;
  region: string;
  environment: string;
}

export const getEnvironmentConfig = (): EnvironmentConfig => {
  // Get values from Vite environment variables
  const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000').replace(/\/$/, '');
  const config: EnvironmentConfig = {
    apiUrl: baseUrl,
    userPoolId: import.meta.env.VITE_USER_POOL_ID || '',
    userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID || '',
    region: import.meta.env.VITE_REGION || 'us-east-1',
    environment: import.meta.env.VITE_ENVIRONMENT || 'dev',
  };

  // Validate required configuration
  if (!config.userPoolId || !config.userPoolClientId) {
    console.warn('Missing required AWS Cognito configuration');
  }

  return config;
};

export const config = getEnvironmentConfig(); 