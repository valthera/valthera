import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { User, Shield, Bell, Save } from 'lucide-react';
import { Progress } from '../components/ui/progress';

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
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Account Information */}
      <Card className="border">
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Email</div>
              <div className="text-sm text-muted-foreground">{user?.email}</div>
            </div>
            <Button variant="outline" size="sm">
              Change Email
            </Button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Password</div>
              <p className="text-xs text-muted-foreground">
                Last changed: {lastPasswordChange || 'Never'}
              </p>
            </div>
            <Button variant="outline" size="sm">
              Change Password
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card className="border">
        <CardHeader>
          <CardTitle>Notification Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-foreground">Email Notifications</div>
              <div className="text-sm text-muted-foreground">
                Receive email updates about your account and projects
              </div>
            </div>
            <Switch checked={emailNotifications} onCheckedChange={setEmailNotifications} />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-foreground">Training Completion</div>
              <div className="text-sm text-muted-foreground">
                Get notified when model training completes
              </div>
            </div>
            <Switch checked={trainingNotifications} onCheckedChange={setTrainingNotifications} />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-foreground">Usage Alerts</div>
              <div className="text-sm text-muted-foreground">
                Receive alerts when approaching usage limits
              </div>
            </div>
            <Switch checked={usageAlerts} onCheckedChange={setUsageAlerts} />
          </div>
        </CardContent>
      </Card>

      {/* API Usage */}
      <Card className="border">
        <CardHeader>
          <CardTitle>API Usage</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Current Month</div>
              <span className="text-sm text-muted-foreground">
                {apiUsage.currentMonth} / {apiUsage.monthlyLimit} requests
              </span>
            </div>
            <Progress value={(apiUsage.currentMonth / apiUsage.monthlyLimit) * 100} className="w-32" />
          </div>
          
          <div className="text-sm text-muted-foreground">
            <p className="text-xs text-muted-foreground">
              Usage resets on the 1st of each month. Upgrade your plan for higher limits.
            </p>
          </div>
          
          <div className="text-sm text-muted-foreground">
            <div className="font-medium">Plan Details</div>
            <div className="text-sm text-muted-foreground">
              Current Plan: {currentPlan} • Next Billing: {nextBillingDate}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card className="border">
        <CardHeader>
          <CardTitle>Data & Privacy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium text-foreground mb-2">Data Retention</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Training data: 90 days</li>
              <li>• Model artifacts: 1 year</li>
              <li>• API logs: 30 days</li>
              <li>• User data: Until account deletion</li>
            </ul>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Data Export</div>
              <div className="text-sm text-muted-foreground">
                Download all your data and models
              </div>
            </div>
            <Button variant="outline" size="sm">
              Export Data
            </Button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Delete Account</div>
              <div className="text-sm text-muted-foreground">
                Permanently delete your account and all data
              </div>
            </div>
            <Button variant="destructive" size="sm">
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Save className="mr-2 h-4 w-4" />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}