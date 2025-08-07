// Utility functions for feature flag URL management

/**
 * Get all feature flags from URL parameters
 * @returns Array of flag names that are enabled via URL
 */
export function getUrlFlags(): string[] {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.getAll('flag');
}

/**
 * Add a feature flag to the current URL
 * @param flagName - The name of the flag to enable
 * @param replace - Whether to replace the current URL (default: false)
 */
export function addUrlFlag(flagName: string, replace: boolean = false): void {
  const url = new URL(window.location.href);
  url.searchParams.append('flag', flagName);
  
  if (replace) {
    window.history.replaceState({}, '', url.toString());
  } else {
    window.history.pushState({}, '', url.toString());
  }
}

/**
 * Remove a feature flag from the current URL
 * @param flagName - The name of the flag to remove
 * @param replace - Whether to replace the current URL (default: false)
 */
export function removeUrlFlag(flagName: string, replace: boolean = false): void {
  const url = new URL(window.location.href);
  const flags = url.searchParams.getAll('flag');
  const newFlags = flags.filter(flag => flag !== flagName);
  
  // Remove all flag parameters
  url.searchParams.delete('flag');
  
  // Add back the remaining flags
  newFlags.forEach(flag => {
    url.searchParams.append('flag', flag);
  });
  
  if (replace) {
    window.history.replaceState({}, '', url.toString());
  } else {
    window.history.pushState({}, '', url.toString());
  }
}

/**
 * Clear all feature flags from the URL
 * @param replace - Whether to replace the current URL (default: false)
 */
export function clearUrlFlags(replace: boolean = false): void {
  const url = new URL(window.location.href);
  url.searchParams.delete('flag');
  
  if (replace) {
    window.history.replaceState({}, '', url.toString());
  } else {
    window.history.pushState({}, '', url.toString());
  }
}

/**
 * Check if a specific flag is enabled via URL
 * @param flagName - The name of the flag to check
 * @returns True if the flag is enabled via URL
 */
export function isUrlFlagEnabled(flagName: string): boolean {
  const urlFlags = getUrlFlags();
  return urlFlags.includes(flagName);
}

/**
 * Generate a URL with specific feature flags enabled
 * @param flags - Array of flag names to enable
 * @param baseUrl - Base URL (defaults to current location)
 * @returns URL string with the specified flags
 */
export function generateUrlWithFlags(flags: string[], baseUrl?: string): string {
  const url = new URL(baseUrl || window.location.href);
  url.searchParams.delete('flag'); // Clear existing flags
  
  flags.forEach(flag => {
    url.searchParams.append('flag', flag);
  });
  
  return url.toString();
} 