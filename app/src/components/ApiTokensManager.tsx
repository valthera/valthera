import { useAuth } from '../contexts/AuthContext'

export function ApiTokensManager() {
  const { user } = useAuth()

  if (!user) {
    return <div>Please sign in to manage API tokens.</div>
  }

  return (
    <div className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <div className="w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center mt-0.5">
            <span className="text-xs font-bold text-yellow-900">!</span>
          </div>
          <div className="text-sm">
            <p className="font-medium text-gray-900 mb-1">API Token Management Unavailable</p>
            <p className="text-gray-600">
              API token management functionality has been temporarily disabled. 
              The account service has been removed from the backend infrastructure.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Current Status</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">User Email:</label>
            <p className="text-gray-900">{user.email}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Subscription Status:</label>
            <span
              className={`px-2 py-1 text-xs rounded-full ${
                user.subscription_status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {user.subscription_status || 'inactive'}
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Plan Type:</label>
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              {user.plan_type || 'free'}
            </span>
          </div>

          {user.api_key && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Current API Key:</label>
              <p className="text-gray-900 font-mono text-sm">{user.api_key}</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">What's Changed?</h3>
        <div className="space-y-3 text-sm text-gray-600">
          <p>
            • The account management lambda function has been removed from the backend
          </p>
          <p>
            • API token creation and management is no longer available
          </p>
          <p>
            • User profiles are now managed through Cognito user attributes only
          </p>
          <p>
            • For API access, please contact support for alternative authentication methods
          </p>
        </div>
      </div>
    </div>
  )
} 