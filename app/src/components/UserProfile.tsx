import { useAuth } from '../contexts/AuthContext'

export function UserProfile() {
  const { user } = useAuth()

  if (!user) {
    return <div>Please sign in to view your profile.</div>
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">User Profile</h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold">Profile Information</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <p className="text-gray-900">{user.email}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User ID
            </label>
            <p className="text-gray-900">{user.id}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Member Since
            </label>
            <p className="text-gray-900">
              {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subscription Status
            </label>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plan Type
            </label>
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              {user.plan_type || 'free'}
            </span>
          </div>

          {user.stripe_customer_id && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stripe Customer ID
              </label>
              <p className="text-gray-900">{user.stripe_customer_id}</p>
            </div>
          )}

          {user.api_key && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key
              </label>
              <p className="text-gray-900 font-mono text-sm">{user.api_key}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 