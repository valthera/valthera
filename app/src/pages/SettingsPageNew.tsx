import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { User, Shield, Bell, Save } from 'lucide-react';

export function SettingsPageNew() {
  const { user } = useAuth();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [trainingNotifications, setTrainingNotifications] = useState(true);
  const [usageAlerts, setUsageAlerts] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate save operation
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-black">Settings</h1>
        <p className="text-gray-600 mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Account Information */}
      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="mr-2 h-5 w-5" />
            Account Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              value={user?.email || ''}
              disabled
              className="bg-gray-50"
            />
            <p className="text-xs text-gray-500">
              Email address cannot be changed. Contact support if needed.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="userId">User ID</Label>
            <div className="flex items-center space-x-2">
              <Input
                id="userId"
                value="user-12345"
                disabled
                className="bg-gray-50 font-mono text-sm"
              />
              <Badge variant="secondary">Read-only</Badge>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Account Status</Label>
            <div className="flex items-center space-x-2">
              <Badge className="bg-green-100 text-green-800">
                <Shield className="mr-1 h-3 w-3" />
                Active
              </Badge>
              <span className="text-sm text-gray-600">
                Account is in good standing
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Bell className="mr-2 h-5 w-5" />
            Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-black">Email Notifications</div>
              <div className="text-sm text-gray-600">
                Receive general notifications via email
              </div>
            </div>
            <Switch
              checked={emailNotifications}
              onCheckedChange={setEmailNotifications}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-black">Training Completion</div>
              <div className="text-sm text-gray-600">
                Get notified when training jobs complete
              </div>
            </div>
            <Switch
              checked={trainingNotifications}
              onCheckedChange={setTrainingNotifications}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-black">Usage Alerts</div>
              <div className="text-sm text-gray-600">
                Alerts when approaching usage limits
              </div>
            </div>
            <Switch
              checked={usageAlerts}
              onCheckedChange={setUsageAlerts}
            />
          </div>
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="mr-2 h-5 w-5" />
            API Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Default Model</Label>
            <div className="flex items-center space-x-2">
              <Badge className="bg-blue-100 text-blue-800">VJEPA2</Badge>
              <span className="text-sm text-gray-600">
                All video embeddings use VJEPA2 by default
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Model cannot be changed in the current version
            </p>
          </div>

          <div className="space-y-2">
            <Label>Rate Limiting</Label>
            <div className="text-sm text-gray-600">
              No rate limits currently enforced. Usage is tracked for billing purposes.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="mr-2 h-5 w-5" />
            Data & Privacy
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-black mb-2">Data Retention</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Uploaded videos are processed and then deleted after 30 days</li>
              <li>• Generated embeddings are stored indefinitely</li>
              <li>• API usage logs are retained for 90 days</li>
              <li>• Billing records are kept for 7 years</li>
            </ul>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-800 mb-2">Data Processing</h4>
            <p className="text-sm text-blue-700">
              All video processing happens in secure, isolated environments. 
              Your data is never shared with third parties and is processed 
              only for the purpose of generating embeddings and training classifiers.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-black text-white hover:bg-gray-800"
        >
          <Save className="mr-2 h-4 w-4" />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}