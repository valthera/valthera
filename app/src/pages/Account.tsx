import { useState } from 'react'
import { UserProfile } from '../components/UserProfile'
import { ApiTokensManager } from '../components/ApiTokensManager'
import { useAuth } from '../contexts/AuthContext'

export function Account() {
  const { user, loading } = useAuth()
  const [activeTab, setActiveTab] = useState<'profile' | 'tokens'>('profile')

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Please Sign In</h2>
          <p className="text-gray-600">You need to be signed in to access your account.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Account Settings</h1>
          <p className="text-gray-600 mt-2">
            Manage your profile and API tokens
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('profile')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'profile'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => setActiveTab('tokens')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'tokens'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              API Tokens
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'profile' && <UserProfile />}
          {activeTab === 'tokens' && <ApiTokensManager />}
        </div>
      </div>
    </div>
  )
} 