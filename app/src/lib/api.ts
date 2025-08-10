// API functions for real backend integration

// Debug function to check authentication state
export async function debugAuthState() {
  try {
    const { fetchAuthSession } = await import('aws-amplify/auth');
    const authSession = await fetchAuthSession();
    console.log('🔍 Debug Auth State:');
    console.log('Auth Session:', authSession);
    console.log('Tokens:', authSession.tokens);
    console.log('ID Token:', authSession.tokens?.idToken);
    console.log('Access Token:', authSession.tokens?.accessToken);
    return authSession;
  } catch (error) {
    console.error('❌ Error fetching auth session:', error);
    return null;
  }
}

// API request helper function
async function apiRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://oi6057c2vf.execute-api.us-east-1.amazonaws.com/dev';
  // Ensure base URL doesn't end with slash and url starts with slash
  const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const cleanUrl = url.startsWith('/') ? url : `/${url}`;
  const fullUrl = `${cleanBaseUrl}${cleanUrl}`;
  
  // Build authentication headers
  const authHeaders: Record<string, string> = {};
  
  try {
    // Add authorization header if we have a session
    const { fetchAuthSession } = await import('aws-amplify/auth');
    const authSession = await fetchAuthSession();
    const idToken = authSession.tokens?.idToken?.toString();
    
    if (idToken) {
      authHeaders['Authorization'] = `Bearer ${idToken}`;
      console.log('Added auth token to request');
      console.log('Token length:', idToken.length);
      console.log('Token preview:', idToken.substring(0, 50) + '...');
    } else {
      console.log('No auth token available');
      console.log('Auth session:', authSession);
    }
  } catch (error) {
    console.error('Error fetching auth session:', error);
  }
  
  // Merge headers and set Content-Type only when appropriate
  const isFormData = options.body instanceof FormData;
  const mergedHeaders: Record<string, string> = {
    ...authHeaders,
    ...(options.headers as Record<string, string> | undefined),
  };

  // Only set Content-Type to application/json when body is JSON-like and caller hasn't specified it
  const hasExplicitContentType = Object.keys(mergedHeaders)
    .some((key) => key.toLowerCase() === 'content-type');
  if (!isFormData && options.body !== undefined && !hasExplicitContentType) {
    mergedHeaders['Content-Type'] = 'application/json';
  }

  const defaultOptions: RequestInit = {
    ...options,
    headers: mergedHeaders,
  };

  try {
    console.log('Making API request to:', fullUrl);
    console.log('Request headers:', defaultOptions.headers);
    const response = await fetch(fullUrl, defaultOptions);
    
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('HTTP error response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    
    const contentType = response.headers.get('content-type');
    console.log('Content-Type:', contentType);
    
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('API response data:', data);
      return data;
    } else {
      // Handle non-JSON responses
      const text = await response.text();
      console.warn('API returned non-JSON response:', text);
      throw new Error('Invalid response format from server');
    }
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  videoCount: number;
  hasDroidDataset: boolean;
  status: 'active' | 'training' | 'completed';
  linkedDataSources: string[];
}

export interface Concept {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  sampleCount: number;
  uploadedAt: string;
  slug?: string;
}

export interface TrainingJob {
  id: string;
  projectId: string;
  status: 'preprocessing' | 'training' | 'validating' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  logs: string[];
  config?: {
    modelType: string;
    hyperparameters: object;
    dataSources: string[];
  };
}

export interface APIEndpoint {
  id: string;
  projectId: string;
  conceptId: string;
  classifierName: string;
  accuracy: number;
  url: string;
  status: 'ready' | 'training' | 'failed';
  createdAt: string;
  usageMetrics: {
    totalCalls: number;
    lastUsed?: string;
    errorRate: number;
  };
}

export interface VideoFile {
  id?: string;
  fileName: string;
  fileSize: number;
  uploadDate: string;
  s3Key: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  metadata: {
    width?: number;
    height?: number;
    fps?: number;
    format?: string;
  };
  // Additional properties for linked videos
  size?: string;
  source?: string;
}

export interface DataSource {
  id: string;
  name: string;
  description?: string;
  folderPath: string;
  videoCount: number;
  totalSize: number;
  createdAt: string;
  updatedAt: string;
  files: VideoFile[];
}

export interface Endpoint {
  id: string;
  projectId: string;
  classifierName: string;
  accuracy: number;
  url: string;
  status: 'ready' | 'training' | 'failed';
  createdAt: string;
}

export interface ApiKey {
  id: string; // Alias for key_id for React component compatibility
  key_id: string;
  name: string;
  key?: string; // For display purposes (only available when creating)
  scopes: string[];
  created_at: number;
  createdAt: string; // ISO string for React component compatibility
  expires_at?: number;
  expiresAt?: string; // ISO string for React component compatibility
  revoked: boolean;
  is_valid: boolean;
  is_expired: boolean;
  usageCount?: number; // For display purposes
  lastUsed?: string; // ISO string for display purposes
}



// API functions
export const api = {
  // Projects
  getProjects: async (): Promise<Project[]> => {
    console.log('Making API call to get projects...');
    const response = await apiRequest<any>('/api/projects');
    console.log('API response for getProjects:', response);
    if (Array.isArray(response)) {
      return response as Project[];
    }
    if (response && Array.isArray(response.projects)) {
      return response.projects as Project[];
    }
    console.warn('Unexpected projects response shape, defaulting to empty array');
    return [];
  },

  createProject: async (data: { name: string; description: string; hasDroidDataset: boolean; linkedDataSources: string[] }): Promise<Project> => {
    console.log('Making API call to create project:', data);
    const newProject = await apiRequest<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    console.log('API response for createProject:', newProject);
    return newProject;
  },

  uploadProjectVideos: async (projectId: string, files: File[]): Promise<void> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    await apiRequest<void>(`/api/projects/${projectId}/videos`, {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for FormData
    });
  },

  // Concepts
  getConcepts: async (projectId: string): Promise<Concept[]> => {
    const response = await apiRequest<{concepts: Concept[], count: number}>(`/api/projects/${projectId}/concepts`);
    return response.concepts.map(c => ({
      ...c,
      slug: c.name.toLowerCase().replace(/\s+/g, '-')
    }));
  },

  createConcept: async (projectId: string, name: string): Promise<Concept> => {
    const response = await apiRequest<Concept>(`/api/projects/${projectId}/concepts`, {
      method: 'POST',
      body: JSON.stringify({ name })
    });
    return {
      ...response,
      slug: response.name.toLowerCase().replace(/\s+/g, '-')
    };
  },

  uploadConceptSamples: async (conceptId: string, files: File[]): Promise<void> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    await apiRequest<void>(`/api/concepts/${conceptId}/samples`, {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for FormData
    });
  },

  // Training
  startTraining: async (projectId: string): Promise<TrainingJob> => {
    return await apiRequest<TrainingJob>(`/api/projects/${projectId}/training`, {
      method: 'POST',
      body: JSON.stringify({})
    });
  },

  getTrainingStatus: async (jobId: string): Promise<TrainingJob> => {
    return await apiRequest<TrainingJob>(`/api/training/${jobId}`);
  },

  // Endpoints
  getEndpoints: async (projectId: string): Promise<Endpoint[]> => {
    return await apiRequest<Endpoint[]>(`/api/projects/${projectId}/endpoints`);
  },

  testEndpoint: async (endpointId: string, videoFile: File): Promise<{ prediction: string; confidence: number }> => {
    const formData = new FormData();
    formData.append('video', videoFile);
    
    return await apiRequest<{ prediction: string; confidence: number }>(`/api/endpoints/${endpointId}/test`, {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for FormData
    });
  },

  // API Keys
  getApiKeys: async (): Promise<ApiKey[]> => {
    const response = await apiRequest<{keys: ApiKey[], message: string, count: number}>('/api/keys');
    return response.keys;
  },

  createApiKey: async (name: string, scopes: string[]): Promise<ApiKey> => {
    const response = await apiRequest<{
      message: string;
      key_id: string;
      display_key: string;
      name: string;
      scopes: string[];
      created_at: number;
      expires_at?: number;
    }>('/api/keys', {
      method: 'POST',
      body: JSON.stringify({ name, scopes })
    });
    
    // Convert the response to match the ApiKey interface
    return {
      key_id: response.key_id,
      name: response.name,
      scopes: response.scopes,
      created_at: response.created_at,
      expires_at: response.expires_at,
      revoked: false,
      is_valid: true,
      is_expired: false
    };
  },

  deleteApiKey: async (keyId: string): Promise<void> => {
    await apiRequest<void>(`/api/keys/${keyId}`, {
      method: 'DELETE'
    });
  },

  revokeApiKey: async (keyId: string): Promise<void> => {
    await apiRequest<void>(`/api/keys/${keyId}/revoke`, {
      method: 'POST'
    });
  },



  // New API methods for enhanced schema
  projects: {
    create: async (data: Omit<Project, 'id' | 'createdAt' | 'videoCount' | 'status'>) => {
      console.log('Making API call to create project via projects.create:', data);
      const newProject = await apiRequest<Project>('/api/projects', { method: 'POST', body: JSON.stringify(data) });
      console.log('API response for projects.create:', newProject);
      return newProject;
    },
    
    list: async () => {
      console.log('Making API call to list projects...');
      const data = await apiRequest<Project[]>('/api/projects');
      console.log('API response for projects.list:', data);
      return data;
    },
    
    get: (id: string) => apiRequest<Project>(`/api/projects/${id}`),
    
    update: (id: string, data: Partial<Project>) => 
      apiRequest<Project>(`/api/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    
    delete: (id: string) => 
      apiRequest<void>(`/api/projects/${id}`, { method: 'DELETE' })
  },

  concepts: {
    create: async (projectId: string, data: Omit<Concept, 'id' | 'projectId' | 'uploadedAt' | 'sampleCount' | 'slug'>) => {
      const response = await apiRequest<any>(`/api/projects/${projectId}/concepts`, { method: 'POST', body: JSON.stringify(data) });
      return {
        ...response,
        slug: response.name.toLowerCase().replace(/\s+/g, '-')
      };
    },
    
    list: async (projectId: string) => {
      const response = await apiRequest<{concepts: any[], count: number}>(`/api/projects/${projectId}/concepts`);
      return response.concepts.map(c => ({
        ...c,
        slug: c.name.toLowerCase().replace(/\s+/g, '-')
      }));
    },
    
    get: (projectId: string, id: string) => apiRequest<Concept>(`/api/projects/${projectId}/concepts/${id}`),
    
    update: async (projectId: string, id: string, data: Partial<Concept>) => {
      const response = await apiRequest<any>(`/api/projects/${projectId}/concepts/${id}`, { method: 'PUT', body: JSON.stringify(data) });
      return {
        ...response,
        slug: response.name.toLowerCase().replace(/\s+/g, '-')
      };
    },
    
    delete: (projectId: string, id: string) =>
      apiRequest<void>(`/api/projects/${projectId}/concepts/${id}`, { method: 'DELETE' }),

    // Video linking methods
    linkVideos: (projectId: string, conceptId: string, videoIds: string[]) =>
      apiRequest<void>(`/api/projects/${projectId}/concepts/${conceptId}/videos`, {
        method: 'POST',
        body: JSON.stringify({ videoIds })
      }),
    
    unlinkVideo: (projectId: string, conceptId: string, videoId: string) =>
      apiRequest<void>(`/api/projects/${projectId}/concepts/${conceptId}/videos/${videoId}`, {
        method: 'DELETE'
      }),
    
    getLinkedVideos: (projectId: string, conceptId: string) =>
      apiRequest<{linkedVideos: VideoFile[], count: number}>(`/api/projects/${projectId}/concepts/${conceptId}/videos`),
    
    getVideoStreamUrl: async (videoId: string) => {
      // Get presigned URL for direct S3 access
      
      try {
        // Get authentication token
        const { fetchAuthSession } = await import('aws-amplify/auth');
        const authSession = await fetchAuthSession();
        const idToken = authSession.tokens?.idToken?.toString();
        
        if (idToken) {
          // Use the presigned URL endpoint instead of streaming
          const response = await apiRequest<{downloadUrl: string}>(`/api/behaviors/videos/${videoId}/url`);
          return response.downloadUrl;
        } else {
          console.warn('No auth token available for video streaming');
          // Use direct S3 URL for local development
          return `http://localhost:4566/valthera-dev-videos-local/${videoId}`;
        }
      } catch (error) {
        console.error('Error getting presigned URL for video:', error);
        // Fallback to direct S3 URL for local development
        return `http://localhost:4566/valthera-dev-videos-local/${videoId}`;
      }
    },
  },

  dataSources: {
    create: (data: { name: string; description?: string }) =>
      apiRequest<DataSource>('/api/datasources', { method: 'POST', body: JSON.stringify(data) }),
    
    list: async () => {
      const response = await apiRequest<any>('/api/datasources');
      if (Array.isArray(response)) return response as DataSource[];
      if (response && Array.isArray(response.datasources)) return response.datasources as DataSource[];
      console.warn('Unexpected datasources response shape');
      return [] as DataSource[];
    },
    
    get: (id: string) => apiRequest<DataSource>(`/api/datasources/${id}`),
    
    delete: (id: string) => 
      apiRequest<void>(`/api/datasources/${id}`, { method: 'DELETE' }),
    
    // Generate presigned URL for secure file upload
    generateUploadUrl: (id: string, fileData: { filename: string; contentType?: string; fileSize: number }) =>
      apiRequest<{
        fileId: string;
        uploadUrl: string;
        fields: Record<string, string>;
        s3Key: string;
        expires: string;
      }>(`/api/datasources/${id}/upload-url`, { 
        method: 'POST', 
        body: JSON.stringify(fileData) 
      }),
    
    // Confirm upload completion
    confirmUpload: (id: string, uploadData: { fileId: string; filename: string; s3Key: string }) =>
      apiRequest<VideoFile>(`/api/datasources/${id}/confirm-upload`, { 
        method: 'POST', 
        body: JSON.stringify(uploadData) 
      }),
    
    // Delete a specific file
    deleteFile: (id: string, fileId: string) =>
      apiRequest<void>(`/api/datasources/${id}/files/${fileId}`, { method: 'DELETE' }),
    
    // Direct upload to Lambda function
    uploadFile: (id: string, fileData: { filename: string; content: string }) => {
      return apiRequest<VideoFile>(`/api/datasources/${id}/upload`, { 
        method: 'POST', 
        body: JSON.stringify(fileData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
  },

  training: {
    create: (projectId: string, trainingConfig: { modelType: string; hyperparameters: object; dataSources: string[] }) => {
      return apiRequest<TrainingJob>(`/api/projects/${projectId}/training`, { 
        method: 'POST', 
        body: JSON.stringify(trainingConfig) 
      });
    },
    
    list: (projectId: string) => apiRequest<TrainingJob[]>(`/api/projects/${projectId}/training`),
    
    get: (projectId: string, id: string) => apiRequest<TrainingJob>(`/api/projects/${projectId}/training/${id}`)
  },

  endpoints: {
    create: (projectId: string, data: { behaviorId: string; classifierName: string; accuracy: number; url: string; status: string }) =>
      apiRequest<APIEndpoint>(`/api/projects/${projectId}/endpoints`, { method: 'POST', body: JSON.stringify(data) }),
    
    list: (projectId: string) => apiRequest<APIEndpoint[]>(`/api/projects/${projectId}/endpoints`),
    
    classify: (endpointId: string, videoData: Blob) => {
      const formData = new FormData();
      formData.append('video', videoData);
      return apiRequest<{ prediction: string; confidence: number }>(`/api/classify/${endpointId}`, { 
        method: 'POST', 
        body: formData,
        headers: {} // Let browser set Content-Type for FormData
      });
    }
  },

  // Observations API (maps to concepts)
  observations: {
    get: (projectId: string, observationId: string) => 
      apiRequest<Concept>(`/api/projects/${projectId}/concepts/${observationId}`),
    
    getLinkedVideos: (projectId: string, observationId: string) =>
      apiRequest<{linkedVideos: VideoFile[], count: number}>(`/api/projects/${projectId}/concepts/${observationId}/videos`),
    
    unlinkVideo: (projectId: string, observationId: string, videoId: string) =>
      apiRequest<void>(`/api/projects/${projectId}/concepts/${observationId}/videos/${videoId}`, {
        method: 'DELETE'
      }),
    
    linkVideos: (projectId: string, observationId: string, videoIds: string[]) =>
      apiRequest<void>(`/api/projects/${projectId}/concepts/${observationId}/videos`, {
        method: 'POST',
        body: JSON.stringify({ videoIds })
      }),
    
    getVideoStreamUrl: async (videoId: string) => {
      // Get presigned URL for direct S3 access
      
      try {
        // Get authentication token
        const { fetchAuthSession } = await import('aws-amplify/auth');
        const authSession = await fetchAuthSession();
        const idToken = authSession.tokens?.idToken?.toString();
        
        if (idToken) {
          // Use the presigned URL endpoint instead of streaming
          const response = await apiRequest<{downloadUrl: string}>(`/api/behaviors/videos/${videoId}/url`);
          return response.downloadUrl;
        } else {
          console.warn('No auth token available for video streaming');
          // Use direct S3 URL for local development
          return `http://localhost:4566/valthera-dev-videos-local/${videoId}`;
        }
      } catch (error) {
        console.error('Error getting presigned URL for video:', error);
        // Fallback to direct S3 URL for local development
        return `http://localhost:4566/valthera-dev-videos-local/${videoId}`;
      }
    },
  }
};

// Test function to verify API connectivity
export async function testApiConnection() {
  try {
    console.log('🧪 Testing API connection...');
    const response = await apiRequest<any>('/api/projects');
    console.log('✅ API connection successful:', response);
    return true;
  } catch (error) {
    console.error('❌ API connection failed:', error);
    return false;
  }
}