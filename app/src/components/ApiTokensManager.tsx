import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'

// Updated API Key interface to match backend
interface ApiKey {
  key_id: string
  name: string
  scopes: string[]
  created_at: number
  expires_at?: number
  revoked: boolean
  is_valid: boolean
  is_expired: boolean
}

// Core scopes for open source project
const AVAILABLE_SCOPES = {
  'read': 'Read access to projects and concepts',
  'write': 'Create and update projects and concepts',
  'training': 'Start and manage training jobs',
  'endpoints': 'Access to classification endpoints'
}

export function ApiTokensManager() {
  const { user } = useAuth()
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [selectedScopes, setSelectedScopes] = useState<string[]>(['read'])
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      loadApiKeys()
    }
  }, [user])

  const loadApiKeys = async () => {
    try {
      setLoading(true)
      const keys = await api.getApiKeys()
      setApiKeys(keys)
    } catch (error) {
      console.error('Failed to load API keys:', error)
    } finally {
      setLoading(false)
    }
  }

  const createApiKey = async () => {
    if (!newKeyName.trim() || selectedScopes.length === 0) return
    
    try {
      setCreating(true)
      const newKey = await api.createApiKey(newKeyName.trim(), selectedScopes)
      setNewlyCreatedKey(newKey.key)
      setNewKeyName('')
      setSelectedScopes(['read'])
      setShowCreateForm(false)
      await loadApiKeys()
    } catch (error) {
      console.error('Failed to create API key:', error)
    } finally {
      setCreating(false)
    }
  }

  const revokeApiKey = async (keyId: string) => {
    try {
      await api.revokeApiKey(keyId)
      await loadApiKeys()
    } catch (error) {
      console.error('Failed to revoke API key:', error)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString()
  }

  if (!user) {
    return <div>Please sign in to manage API tokens.</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">API Tokens</h2>
          <p className="text-gray-600 mt-1">
            Manage your API tokens for accessing the Valthera Perception API
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          Create New Token
        </button>
      </div>

      {/* Create New Token Form */}
      {showCreateForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Create New API Token</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Token Name
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production API Key"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Permissions (Scopes)
              </label>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(AVAILABLE_SCOPES).map(([scope, description]) => (
                  <label key={scope} className="flex items-start space-x-2">
                    <input
                      type="checkbox"
                      checked={selectedScopes.includes(scope)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedScopes([...selectedScopes, scope])
                        } else {
                          setSelectedScopes(selectedScopes.filter(s => s !== scope))
                        }
                      }}
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div className="text-sm">
                      <span className="font-medium text-gray-900">{scope}</span>
                      <p className="text-gray-500 text-xs">{description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                onClick={createApiKey}
                disabled={creating || !newKeyName.trim() || selectedScopes.length === 0}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium"
              >
                {creating ? 'Creating...' : 'Create Token'}
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Newly Created Key Display */}
      {newlyCreatedKey && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <div className="w-5 h-5 bg-green-400 rounded-full flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-green-900">✓</span>
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-green-900 mb-2">API Token Created Successfully!</h3>
              <p className="text-green-700 text-sm mb-3">
                Copy this token now - it won't be shown again for security reasons.
              </p>
              <div className="bg-white border border-green-200 rounded p-3 flex items-center justify-between">
                <code className="text-sm text-green-800 font-mono break-all">
                  {newlyCreatedKey}
                </code>
                <button
                  onClick={() => copyToClipboard(newlyCreatedKey)}
                  className="ml-3 bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                >
                  Copy
                </button>
              </div>
            </div>
            <button
              onClick={() => setNewlyCreatedKey(null)}
              className="text-green-600 hover:text-green-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* API Keys List */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Your API Tokens</h3>
        </div>
        
        {loading ? (
          <div className="p-6 text-center text-gray-500">Loading...</div>
        ) : apiKeys.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No API tokens found. Create your first token to get started.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {apiKeys.map((key) => (
              <div key={key.key_id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-medium text-gray-900">{key.name}</h4>
                      <div className="flex gap-2">
                        {key.is_valid ? (
                          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                            {key.revoked ? 'Revoked' : 'Expired'}
                          </span>
                        )}
                        {key.expires_at && (
                          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                            Expires {formatDate(key.expires_at)}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600 mb-3">
                      Created: {formatDate(key.created_at)}
                    </div>
                    
                    <div className="mb-3">
                      <span className="text-sm font-medium text-gray-700">Permissions:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {key.scopes.map((scope) => (
                          <span
                            key={scope}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                          >
                            {scope}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    {key.is_valid && (
                      <button
                        onClick={() => revokeApiKey(key.key_id)}
                        className="px-3 py-1 text-sm text-red-600 hover:text-red-800 border border-red-200 hover:border-red-300 rounded"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Extensibility Notice */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <div className="w-5 h-5 bg-gray-400 rounded-full flex items-center justify-center mt-0.5">
            <span className="text-xs font-bold text-gray-900">ℹ</span>
          </div>
          <div className="text-sm">
            <p className="font-medium text-gray-900 mb-1">Easy to Extend</p>
            <p className="text-gray-700">
              This API token system is designed to be easily extended with additional features 
              like rate limiting, usage tracking, and team management when needed.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 