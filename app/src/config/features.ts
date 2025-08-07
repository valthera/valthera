// Feature flags configuration
// This file defines all feature flags for the application
// Set to true to enable features, false to disable them

const features = {
  // AI Research Assistant - Main feature flag
  aiResearchAssistant: false,
  
  // Additional feature flags for future use
  newDashboard: false,
  betaChat: false,
  advancedAnalytics: false,
  experimentalFeatures: false,
} as const;

export default features; 