import { Amplify } from 'aws-amplify'

console.log('🚀 COGNITO.TS LOADED!')

// Check if we're in local development mode
const isLocal = import.meta.env.VITE_ENVIRONMENT === 'local' || import.meta.env.NODE_ENV === 'development'
const cognitoEndpoint = import.meta.env.VITE_COGNITO_ENDPOINT

console.log('🌍 RAW ENV VARS:', {
  'import.meta.env': import.meta.env,
  'VITE_COGNITO_USER_POOL_ID': import.meta.env.VITE_COGNITO_USER_POOL_ID,
  'VITE_COGNITO_USER_POOL_CLIENT_ID': import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID
})

console.log('🔍 Environment check:', {
  VITE_ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT,
  NODE_ENV: import.meta.env.NODE_ENV,
  VITE_COGNITO_USER_POOL_ID: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  VITE_COGNITO_USER_POOL_CLIENT_ID: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID,
  isLocal,
  cognitoEndpoint,
  willSetupOverride: isLocal && cognitoEndpoint
})

// Validate required environment variables
const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
const userPoolClientId = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID
const identityPoolId = import.meta.env.VITE_COGNITO_IDENTITY_POOL_ID

if (!userPoolId) {
  throw new Error('VITE_COGNITO_USER_POOL_ID is required')
}

if (!userPoolClientId) {
  throw new Error('VITE_COGNITO_USER_POOL_CLIENT_ID is required')
}

// For local development, identity pool is optional since cognito-local doesn't support it
if (!identityPoolId && !isLocal) {
  throw new Error('VITE_COGNITO_IDENTITY_POOL_ID is required for production')
}

// Set up fetch override for local development
if (isLocal && cognitoEndpoint) {
  console.log('🔧 Setting up fetch override for local Cognito...')
  
  // Override fetch to redirect Cognito requests to local endpoint
  const originalFetch = window.fetch
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString()
    
    // Redirect Cognito requests to local endpoint
    if (url.includes('cognito-idp.amazonaws.com') || url.includes('cognito-idp.local.amazonaws.com')) {
      const newUrl = url.replace(
        /https?:\/\/[^\/]+/,
        cognitoEndpoint
      )
      console.log(`🔄 Redirecting Cognito request: ${url} → ${newUrl}`)
      return originalFetch(newUrl, init)
    }
    
    // Also redirect cognito-identity requests for local development
    if (url.includes('cognito-identity.amazonaws.com')) {
      const newUrl = url.replace(
        /https?:\/\/[^\/]+/,
        cognitoEndpoint
      )
      console.log(`🔄 Redirecting Cognito Identity request: ${url} → ${newUrl}`)
      return originalFetch(newUrl, init)
    }
    
    return originalFetch(input, init)
  }
}

// Cognito configuration for both local and production
const cognitoConfig = {
  Auth: {
    Cognito: {
      userPoolId,
      userPoolClientId,
      // Only include identityPoolId for production (not for local development)
      ...(identityPoolId && !isLocal && { identityPoolId }),
      loginWith: {
        email: true,
        username: false,
      },
      // Explicitly set auth flow for local development
      ...(isLocal && {
        signUpVerificationMethod: 'code',
        userAttributes: {
          email: {
            required: true,
          },
        },
      }),
    },
  },
  // Add AWS configuration for local development
  ...(isLocal && {
    AWS: {
      region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
      credentials: {
        accessKeyId: 'local',
        secretAccessKey: 'local',
      },
      // Configure custom endpoints for local development
      endpoints: {
        'cognito-idp': {
          endpoint: cognitoEndpoint,
          region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
        },
        'cognito-identity': {
          endpoint: cognitoEndpoint,
          region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
        },
      },
    },
  }),
}

// Configure Amplify
Amplify.configure(cognitoConfig)

console.log(`🔧 Amplify configured for ${isLocal ? 'LOCAL' : 'PRODUCTION'} environment`)
console.log(`📋 Using configuration:`, {
  userPoolId,
  userPoolClientId,
  identityPoolId: identityPoolId || 'NOT_USED_FOR_LOCAL',
  endpoint: cognitoEndpoint,
  authFlow: isLocal ? 'USER_PASSWORD_AUTH' : 'USER_SRP_AUTH'
})

if (isLocal) {
  console.log(`🏠 Using local Cognito endpoint: ${cognitoEndpoint}`)
  console.log(`🔄 Fetch override enabled for local development`)
  console.log(`🔐 Using USER_PASSWORD_AUTH flow for local development`)
  console.log(`⚠️  Identity Pool disabled for local development (cognito-local limitation)`)
}

export { Amplify } 