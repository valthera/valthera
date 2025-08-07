import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import features from '../config/features';

// Define the type locally to avoid import issues
type FeatureFlags = {
  aiResearchAssistant: boolean;
  newDashboard: boolean;
  betaChat: boolean;
  advancedAnalytics: boolean;
  experimentalFeatures: boolean;
};

// Function to parse URL parameters and override feature flags
function getFeatureFlagsWithUrlOverrides(): FeatureFlags {
  const urlParams = new URLSearchParams(window.location.search);
  const flagParams = urlParams.getAll('flag'); // Get all flag parameters
  
  // Start with the default features
  const flagsWithOverrides = { ...features };
  
  // Enable all flags specified in URL parameters
  flagParams.forEach(flagParam => {
    if (flagParam in flagsWithOverrides) {
      (flagsWithOverrides as any)[flagParam] = true;
    }
  });
  
  return flagsWithOverrides;
}

// Create the context with the features as default value
const FeatureFlagContext = createContext<FeatureFlags>(features);

// Provider component that wraps the app
function FeatureFlagProvider({ children }: { children: ReactNode }) {
  const [featureFlags, setFeatureFlags] = useState<FeatureFlags>(() => getFeatureFlagsWithUrlOverrides());

  // Update feature flags when URL changes
  useEffect(() => {
    const handleUrlChange = () => {
      setFeatureFlags(getFeatureFlagsWithUrlOverrides());
    };

    // Listen for URL changes
    window.addEventListener('popstate', handleUrlChange);
    
    // Also check on mount and when search params change
    const checkUrlParams = () => {
      const currentFlags = getFeatureFlagsWithUrlOverrides();
      setFeatureFlags(currentFlags);
    };
    
    // Check immediately
    checkUrlParams();
    
    // Set up an observer for URL changes (for SPA navigation)
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      checkUrlParams();
    };
    
    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      checkUrlParams();
    };

    return () => {
      window.removeEventListener('popstate', handleUrlChange);
      history.pushState = originalPushState;
      history.replaceState = originalReplaceState;
    };
  }, []);

  return (
    <FeatureFlagContext.Provider value={featureFlags}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

// Hook to use feature flags in components
function useFeatureFlags() {
  const context = useContext(FeatureFlagContext);
  if (context === undefined) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider');
  }
  return context;
}

// Helper hook for checking specific feature flags
function useFeatureFlag(flag: keyof FeatureFlags): boolean {
  const flags = useFeatureFlags();
  return flags[flag];
}

export { FeatureFlagProvider, useFeatureFlags, useFeatureFlag }; 