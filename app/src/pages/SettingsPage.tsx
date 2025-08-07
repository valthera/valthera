import { DashboardLayout } from '../components/DashboardLayout'
import { UserProfile } from '../components/UserProfile'

export function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-2">
            Manage your account settings and profile information
          </p>
        </div>
        
        <UserProfile />
      </div>
    </DashboardLayout>
  )
}