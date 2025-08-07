import { useFeatureFlag, useFeatureFlags } from '../contexts/FeatureFlagsContext';
import { Button } from './ui/button';

// Example component showing different ways to use feature flags
export function FeatureFlagExample() {
  // Method 1: Check a specific feature flag
  const isAIAssistantEnabled = useFeatureFlag('aiResearchAssistant');
  const isNewDashboardEnabled = useFeatureFlag('newDashboard');
  
  // Method 2: Get all feature flags
  const allFlags = useFeatureFlags();

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="font-medium mb-4">Feature Flag Examples</h3>
      
      {/* Conditional rendering based on feature flag */}
      {isAIAssistantEnabled && (
        <div className="mb-3 p-3 bg-green-100 border border-green-200 rounded">
          <p className="text-sm text-green-800">
            ✅ AI Research Assistant is enabled
          </p>
        </div>
      )}

      {!isAIAssistantEnabled && (
        <div className="mb-3 p-3 bg-red-100 border border-red-200 rounded">
          <p className="text-sm text-red-800">
            ❌ AI Research Assistant is disabled
          </p>
        </div>
      )}

      {/* Conditional button rendering */}
      {isNewDashboardEnabled && (
        <Button className="mb-3">
          Try New Dashboard
        </Button>
      )}

      {/* Show all feature flags */}
      <div className="mt-4">
        <h4 className="text-sm font-medium mb-2">All Feature Flags:</h4>
        <div className="space-y-1 text-xs">
          {Object.entries(allFlags).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span>{key}:</span>
              <span className={value ? 'text-green-600' : 'text-red-600'}>
                {value ? 'ON' : 'OFF'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 