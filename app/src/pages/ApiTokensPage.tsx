import { ApiTokensManager } from '../components/ApiTokensManager'
import { DashboardLayout } from '../components/DashboardLayout'

export function ApiTokensPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">API Tokens</h1>
          <p className="text-gray-600 mt-2">
            Manage your API tokens for accessing the Valthera Perception API
          </p>
        </div>
        
        <ApiTokensManager />
      </div>
    </DashboardLayout>
  )
} 