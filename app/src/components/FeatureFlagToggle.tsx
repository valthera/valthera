import { useState } from 'react';
import { Button } from './ui/button';
import { useFeatureFlags } from '../contexts/FeatureFlagsContext';
import { Settings, Info, X, Plus } from 'lucide-react';
import features from '../config/features';
import { getUrlFlags, addUrlFlag, removeUrlFlag, clearUrlFlags } from '../utils/featureFlags';

// This component is for development/testing purposes only
// In production, you would typically manage feature flags through a remote service
export function FeatureFlagToggle() {
  const [isOpen, setIsOpen] = useState(false);
  const flags = useFeatureFlags();

  // Only show in development
  if (import.meta.env.PROD) {
    return null;
  }

  // Get URL parameters to show overrides
  const urlFlags = getUrlFlags();
  const hasUrlOverrides = urlFlags.length > 0;

  // Check which flags are overridden by URL
  const getFlagStatus = (flagName: string, currentValue: boolean) => {
    const isOverridden = urlFlags.includes(flagName);
    const originalValue = features[flagName as keyof typeof features];
    
    if (isOverridden) {
      return {
        value: currentValue,
        isOverridden: true,
        originalValue,
        status: 'URL Override'
      };
    }
    
    return {
      value: currentValue,
      isOverridden: false,
      originalValue,
      status: currentValue ? 'ON' : 'OFF'
    };
  };

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <Button
        onClick={() => setIsOpen(!isOpen)}
        size="sm"
        variant="outline"
        className="bg-white shadow-lg"
      >
        <Settings className="h-4 w-4 mr-2" />
        Feature Flags
        {hasUrlOverrides && (
          <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
            {urlFlags.length}
          </span>
        )}
      </Button>

      {isOpen && (
        <div className="absolute bottom-full left-0 mb-2 p-4 bg-white border border-gray-200 rounded-lg shadow-lg min-w-80">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm">Feature Flags (Dev Only)</h3>
            {hasUrlOverrides && (
              <div className="flex items-center text-xs text-blue-600">
                <Info className="h-3 w-3 mr-1" />
                URL Overrides Active
              </div>
            )}
          </div>
          
          <div className="space-y-2 text-xs">
            {Object.entries(flags).map(([key, value]) => {
              const status = getFlagStatus(key, value);
              return (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-gray-700">{key}:</span>
                  <div className="flex items-center space-x-2">
                    {status.isOverridden && (
                      <span className="text-blue-600 text-xs">URL</span>
                    )}
                    <span className={`font-mono ${status.value ? 'text-green-600' : 'text-red-600'}`}>
                      {status.value ? 'ON' : 'OFF'}
                    </span>
                    {status.isOverridden && status.originalValue !== status.value && (
                      <span className="text-gray-400 text-xs">
                        (was {status.originalValue ? 'ON' : 'OFF'})
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          <div className="mt-3 space-y-2 text-xs">
            <p className="text-gray-500">
              Edit features in config/features.ts to change defaults
            </p>
            {hasUrlOverrides && (
              <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-blue-700 font-medium">URL Overrides:</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => clearUrlFlags(true)}
                    className="h-4 w-4 p-0 text-blue-600 hover:text-blue-800"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {urlFlags.map(flag => (
                    <div key={flag} className="flex items-center justify-between">
                      <span className="text-blue-600 text-xs">{flag}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeUrlFlag(flag, true)}
                        className="h-3 w-3 p-0 text-blue-600 hover:text-red-600"
                      >
                        <X className="h-2 w-2" />
                      </Button>
                    </div>
                  ))}
                </div>
                <div className="mt-2 pt-2 border-t border-blue-200">
                  <p className="text-blue-600 text-xs">
                    Add: <code className="bg-blue-100 px-1 rounded">?flag=flagName</code>
                  </p>
                  <p className="text-blue-600 text-xs">
                    Multiple: <code className="bg-blue-100 px-1 rounded">?flag=flag1&flag=flag2</code>
                  </p>
                </div>
              </div>
            )}
            
            {/* Quick add buttons for common flags */}
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-xs text-gray-600 mb-2">Quick Enable:</p>
              <div className="flex flex-wrap gap-1">
                {Object.keys(features).map(flagName => (
                  <Button
                    key={flagName}
                    size="sm"
                    variant="outline"
                    onClick={() => addUrlFlag(flagName, true)}
                    className="text-xs h-6 px-2"
                    disabled={urlFlags.includes(flagName)}
                  >
                    <Plus className="h-2 w-2 mr-1" />
                    {flagName}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 