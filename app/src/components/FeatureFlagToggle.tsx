import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { useFeatureFlags } from '../contexts/FeatureFlagsContext';
import { Settings, Info, X, Plus } from 'lucide-react';
import features from '../config/features';
import { getUrlFlags, addUrlFlag, removeUrlFlag, clearUrlFlags } from '../utils/featureFlags';

interface FeatureFlagToggleProps {
  className?: string;
}

// This component is for development/testing purposes only
// In production, you would typically manage feature flags through a remote service
export function FeatureFlagToggle({ className }: FeatureFlagToggleProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [alignRight, setAlignRight] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const flags = useFeatureFlags();

  // Only show in development
  if (import.meta.env.PROD) {
    return null;
  }

  // Get URL parameters to show overrides
  const urlFlags = getUrlFlags();
  const hasUrlOverrides = urlFlags.length > 0;

  // Flip panel alignment if it would overflow the viewport
  useEffect(() => {
    if (!isOpen) return;

    const recompute = () => {
      try {
        const element = anchorRef.current;
        if (!element) return;
        const rect = element.getBoundingClientRect();
        const panelWidthPx = 320; // ~min-w-80
        const spaceRight = window.innerWidth - rect.right;
        setAlignRight(spaceRight < panelWidthPx + 16);
      } catch {}
    };

    recompute();
    window.addEventListener('resize', recompute);
    return () => window.removeEventListener('resize', recompute);
  }, [isOpen]);

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
    <div ref={anchorRef} className={`relative ${className ?? ''}`}>
      <Button
        onClick={() => setIsOpen(!isOpen)}
        size="sm"
        variant="outline"
        className="bg-background border-border shadow-lg"
      >
        <Settings className="h-4 w-4 mr-2" />
        Feature Flags
        {hasUrlOverrides && (
          <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-200 text-xs rounded-full">
            {urlFlags.length}
          </span>
        )}
      </Button>

      {isOpen && (
        <div className={`absolute bottom-full mb-2 p-4 bg-background border border-border rounded-lg shadow-lg min-w-80 max-w-[90vw] ${alignRight ? 'right-0' : 'left-0'}`}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm">Feature Flags (Dev Only)</h3>
            {hasUrlOverrides && (
              <div className="flex items-center text-xs text-blue-700 dark:text-blue-200">
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
                  <span className="text-muted-foreground">{key}:</span>
                  <div className="flex items-center space-x-2">
                    {status.isOverridden && (
                      <span className="text-blue-700 dark:text-blue-200 text-xs">URL</span>
                    )}
                    <span className={`font-mono ${status.value ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {status.value ? 'ON' : 'OFF'}
                    </span>
                    {status.isOverridden && status.originalValue !== status.value && (
                      <span className="text-muted-foreground text-xs">
                        (was {status.originalValue ? 'ON' : 'OFF'})
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          <div className="mt-3 space-y-2 text-xs">
            <p className="text-muted-foreground">
              Edit features in config/features.ts to change defaults
            </p>
            {hasUrlOverrides && (
              <div className="p-2 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 rounded">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-blue-700 dark:text-blue-200 font-medium">URL Overrides:</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => clearUrlFlags(true)}
                    className="h-4 w-4 p-0 text-blue-700 dark:text-blue-200 hover:text-blue-800 dark:hover:text-blue-300"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {urlFlags.map(flag => (
                    <div key={flag} className="flex items-center justify-between">
                      <span className="text-blue-700 dark:text-blue-200 text-xs">{flag}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeUrlFlag(flag, true)}
                        className="h-3 w-3 p-0 text-blue-700 dark:text-blue-200 hover:text-red-600 dark:hover:text-red-400"
                      >
                        <X className="h-2 w-2" />
                      </Button>
                    </div>
                  ))}
                </div>
                <div className="mt-2 pt-2 border-t border-blue-200 dark:border-blue-900/40">
                  <p className="text-blue-700 dark:text-blue-200 text-xs">
                    Add: <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">?flag=flagName</code>
                  </p>
                  <p className="text-blue-700 dark:text-blue-200 text-xs">
                    Multiple: <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">?flag=flag1&flag=flag2</code>
                  </p>
                </div>
              </div>
            )}
            
            {/* Quick add buttons for common flags */}
            <div className="mt-2 pt-2 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Quick Enable:</p>
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